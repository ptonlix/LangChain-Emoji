# Linux 设置开机自启动

```
#  /usr/lib/systemd/system/langchain-emoji.service
[Unit]
Description=Langchain-Emoji
After=network.target

[Service]
Type=simple
ExecStart=/root/miniconda3/envs/LangChain-Emoji/bin/python -m langchain_emoji

[Install]
WantedBy=multi-user.target
```

```
systemctl enable langchain-emoji.service 开机自启动
systemctl start  langchain-emoji

# 服务启动失败，可通过下面命令查看原因
journalctl -u langchain-emoji -f

```
