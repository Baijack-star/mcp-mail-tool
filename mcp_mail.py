#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Mail Tool MVP
一个基于 Model Context Protocol (MCP) 的邮件工具
支持通过 IMAP/SMTP 协议访问 Outlook/Office365 邮箱

作者: AI-Dev
版本: 1.0.0
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import json
import logging
import datetime
import time
import sys
import os


class MCPMailTool:
    """MCP邮件工具主类"""
    
    def __init__(self, config_file="config.json"):
        """初始化邮件工具
        
        Args:
            config_file (str): 配置文件路径
        """
        self.config = self.load_config(config_file)
        self.imap_conn = None
        self.smtp_conn = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file):
        """加载配置文件
        
        Args:
            config_file (str): 配置文件路径
            
        Returns:
            dict: 配置信息
            
        Raises:
            Exception: 配置文件加载失败
        """
        try:
            if not os.path.exists(config_file):
                raise FileNotFoundError(f"配置文件不存在: {config_file}")
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 验证必需的配置项
            required_fields = ['email', 'password', 'imap_server', 'smtp_server']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"配置文件缺少必需字段: {field}")
                    
            return config
            
        except Exception as e:
            raise Exception(f"CONFIGURATION_ERROR: {str(e)}")
    
    def connect_imap(self):
        """连接IMAP服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.imap_conn = imaplib.IMAP4_SSL(
                self.config['imap_server'], 
                self.config.get('imap_port', 993)
            )
            self.imap_conn.login(self.config['email'], self.config['password'])
            self.logger.info("IMAP连接成功")
            return True
            
        except imaplib.IMAP4.error as e:
            if "authentication failed" in str(e).lower():
                raise Exception(f"AUTHENTICATION_FAILED: {str(e)}")
            else:
                raise Exception(f"IMAP_CONNECTION_FAILED: {str(e)}")
        except Exception as e:
            raise Exception(f"NETWORK_ERROR: {str(e)}")
    
    def connect_smtp(self):
        """连接SMTP服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.smtp_conn = smtplib.SMTP(
                self.config['smtp_server'], 
                self.config.get('smtp_port', 587)
            )
            self.smtp_conn.starttls()
            self.smtp_conn.login(self.config['email'], self.config['password'])
            self.logger.info("SMTP连接成功")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            raise Exception(f"AUTHENTICATION_FAILED: {str(e)}")
        except smtplib.SMTPException as e:
            raise Exception(f"SMTP_CONNECTION_FAILED: {str(e)}")
        except Exception as e:
            raise Exception(f"NETWORK_ERROR: {str(e)}")
    
    def decode_mime_words(self, s):
        """解码MIME编码的字符串
        
        Args:
            s (str): 待解码字符串
            
        Returns:
            str: 解码后的字符串
        """
        try:
            decoded_fragments = decode_header(s)
            decoded_string = ''
            
            for fragment, encoding in decoded_fragments:
                if isinstance(fragment, bytes):
                    if encoding:
                        decoded_string += fragment.decode(encoding)
                    else:
                        decoded_string += fragment.decode('utf-8', errors='ignore')
                else:
                    decoded_string += fragment
                    
            return decoded_string
        except Exception as e:
            self.logger.warning(f"解码失败: {str(e)}")
            return str(s)
    
    def mail_read(self, folder="INBOX", limit=10):
        """读取邮件
        
        Args:
            folder (str): 邮件文件夹名称
            limit (int): 读取邮件数量限制
            
        Returns:
            dict: 包含邮件列表的结果
        """
        retry_count = self.config.get('retry_count', 3)
        retry_delay = self.config.get('retry_delay', 2)
        
        for attempt in range(retry_count):
            try:
                if not self.imap_conn:
                    self.connect_imap()
                
                # 选择文件夹
                status, messages = self.imap_conn.select(folder)
                if status != 'OK':
                    raise Exception(f"FOLDER_NOT_FOUND: 无法访问文件夹 {folder}")
                
                # 搜索邮件
                status, messages = self.imap_conn.search(None, 'ALL')
                if status != 'OK':
                    raise Exception("邮件搜索失败")
                
                message_ids = messages[0].split()
                if not message_ids:
                    return {
                        "success": True,
                        "emails": [],
                        "count": 0
                    }
                
                # 获取最新的邮件（倒序）
                latest_ids = message_ids[-limit:] if len(message_ids) >= limit else message_ids
                latest_ids.reverse()
                
                emails = []
                for msg_id in latest_ids:
                    try:
                        status, msg_data = self.imap_conn.fetch(msg_id, '(RFC822)')
                        if status != 'OK':
                            continue
                            
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # 提取邮件信息
                        subject = self.decode_mime_words(email_message['Subject'] or "无主题")
                        sender = self.decode_mime_words(email_message['From'] or "未知发件人")
                        date = email_message['Date'] or "未知时间"
                        
                        # 提取邮件正文摘要
                        body_summary = self.extract_body_summary(email_message)
                        
                        emails.append({
                            "id": msg_id.decode(),
                            "subject": subject,
                            "sender": sender,
                            "date": date,
                            "body_summary": body_summary
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"处理邮件 {msg_id} 时出错: {str(e)}")
                        continue
                
                return {
                    "success": True,
                    "emails": emails,
                    "count": len(emails)
                }
                
            except Exception as e:
                self.logger.error(f"读取邮件失败 (尝试 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    self.imap_conn = None  # 重置连接
                else:
                    return {
                        "success": False,
                        "error": str(e),
                        "emails": [],
                        "count": 0
                    }
    
    def extract_body_summary(self, email_message, max_length=200):
        """提取邮件正文摘要
        
        Args:
            email_message: 邮件消息对象
            max_length (int): 摘要最大长度
            
        Returns:
            str: 邮件正文摘要
        """
        try:
            body = ""
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
            else:
                charset = email_message.get_content_charset() or 'utf-8'
                body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
            
            # 清理和截断正文
            body = body.strip().replace('\n', ' ').replace('\r', ' ')
            if len(body) > max_length:
                body = body[:max_length] + "..."
                
            return body or "无正文内容"
            
        except Exception as e:
            self.logger.warning(f"提取正文摘要失败: {str(e)}")
            return "正文解析失败"
    
    def mail_send(self, to, subject, body):
        """发送邮件
        
        Args:
            to (str): 收件人邮箱
            subject (str): 邮件主题
            body (str): 邮件正文
            
        Returns:
            dict: 发送结果
        """
        retry_count = self.config.get('retry_count', 3)
        retry_delay = self.config.get('retry_delay', 2)
        
        # 验证邮箱格式
        if '@' not in to or '.' not in to.split('@')[1]:
            return {
                "success": False,
                "error": "INVALID_EMAIL_FORMAT: 收件人邮箱格式无效"
            }
        
        for attempt in range(retry_count):
            try:
                if not self.smtp_conn:
                    self.connect_smtp()
                
                # 创建邮件
                msg = MIMEMultipart()
                msg['From'] = self.config['email']
                msg['To'] = to
                msg['Subject'] = subject
                
                # 添加正文
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # 发送邮件
                text = msg.as_string()
                self.smtp_conn.sendmail(self.config['email'], to, text)
                
                return {
                    "success": True,
                    "message": f"Email sent to {to}",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"发送邮件失败 (尝试 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    self.smtp_conn = None  # 重置连接
                else:
                    return {
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.datetime.now().isoformat()
                    }
    
    def mail_get(self, email_id):
        """获取邮件详细内容
        
        Args:
            email_id (str): 邮件ID
            
        Returns:
            dict: 邮件详细信息
        """
        retry_count = self.config.get('retry_count', 3)
        retry_delay = self.config.get('retry_delay', 2)
        
        for attempt in range(retry_count):
            try:
                if not self.imap_conn:
                    self.connect_imap()
                
                # 选择收件箱
                self.imap_conn.select('INBOX')
                
                # 获取邮件
                status, msg_data = self.imap_conn.fetch(email_id.encode(), '(RFC822)')
                if status != 'OK':
                    raise Exception(f"EMAIL_NOT_FOUND: 邮件ID {email_id} 不存在")
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # 提取完整邮件信息
                subject = self.decode_mime_words(email_message['Subject'] or "无主题")
                sender = self.decode_mime_words(email_message['From'] or "未知发件人")
                to = self.decode_mime_words(email_message['To'] or "未知收件人")
                date = email_message['Date'] or "未知时间"
                
                # 提取完整正文
                body = self.extract_full_body(email_message)
                
                return {
                    "success": True,
                    "id": email_id,
                    "subject": subject,
                    "sender": sender,
                    "to": to,
                    "date": date,
                    "body": body
                }
                
            except Exception as e:
                self.logger.error(f"获取邮件详情失败 (尝试 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    self.imap_conn = None  # 重置连接
                else:
                    return {
                        "success": False,
                        "error": str(e)
                    }
    
    def extract_full_body(self, email_message):
        """提取邮件完整正文
        
        Args:
            email_message: 邮件消息对象
            
        Returns:
            str: 邮件完整正文
        """
        try:
            body = ""
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    elif part.get_content_type() == "text/html" and not body:
                        # 如果没有纯文本，使用HTML（简单处理）
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        # 简单的HTML标签移除
                        import re
                        body = re.sub(r'<[^>]+>', '', html_body)
            else:
                charset = email_message.get_content_charset() or 'utf-8'
                body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
            
            return body.strip() or "无正文内容"
            
        except Exception as e:
            self.logger.warning(f"提取完整正文失败: {str(e)}")
            return "正文解析失败"
    
    def close_connections(self):
        """关闭所有连接"""
        try:
            if self.imap_conn:
                self.imap_conn.close()
                self.imap_conn.logout()
                self.imap_conn = None
                
            if self.smtp_conn:
                self.smtp_conn.quit()
                self.smtp_conn = None
                
            self.logger.info("所有连接已关闭")
        except Exception as e:
            self.logger.warning(f"关闭连接时出错: {str(e)}")


def main():
    """命令行主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python mcp_mail.py read [folder] [limit]")
        print("  python mcp_mail.py send <to> <subject> <body>")
        print("  python mcp_mail.py get <email_id>")
        return
    
    command = sys.argv[1]
    
    try:
        tool = MCPMailTool()
        
        if command == "read":
            folder = sys.argv[2] if len(sys.argv) > 2 else "INBOX"
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            result = tool.mail_read(folder, limit)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "send":
            if len(sys.argv) < 5:
                print("错误: 发送邮件需要收件人、主题和正文")
                return
            to = sys.argv[2]
            subject = sys.argv[3]
            body = sys.argv[4]
            result = tool.mail_send(to, subject, body)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "get":
            if len(sys.argv) < 3:
                print("错误: 获取邮件需要邮件ID")
                return
            email_id = sys.argv[2]
            result = tool.mail_get(email_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        else:
            print(f"未知命令: {command}")
            
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        if 'tool' in locals():
            tool.close_connections()


if __name__ == "__main__":
    main()
