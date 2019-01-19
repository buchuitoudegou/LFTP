# LFTP
udp based reliable File Transport Protocol

## feature
+ base on UDP as transport layer protocol
+ reliable
+ Congestion Control and Flow Control 
+ be able to serve multiple client-end

## dependencies
+ python3.5+
+ OS: Windows10

## run
### run server
Open the server and ensure port `8081` available. Wait for packets coming 
```
python3 server.py
```

### run client
Ensure port `7777` available and exec `python3 client.py`.
```
Ouput: LFTP Client is running...
Ouput: upload(0) or download(1)
Input: 0 (or 1 which is stands for uploading or downloading)
Ouput: please input your filename: 
Input: [filename](which exists in root directory or the FileManage directory)
```
`note`: If user downloads the file whose name is duplicated in root directory, the content of the file will be put behind the content of the file already existing before. The same situation will happen when upload a file with duplicated name in the server-end(the FileManage directory).

### updating
