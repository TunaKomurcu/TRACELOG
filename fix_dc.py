import pathlib
raw = (
 b"version: chr34 3.9chr34\n"
 b"services:\n"
 b"\x20\x20storage:\n"
 b"\x20\x20\x20\x20build: .\n"
 b"\x20\x20\x20\x20ports:\n"
 b"\x20\x20\x20\x20\x20\x20- chr34 8765:8765chr34\n"
 b"\x20\x20\x20\x20volumes:\n"
 b"\x20\x20\x20\x20\x20\x20- sazabi_data:/data\n"
 b"\x20\x20\x20\x20env_file:\n"
 b"\x20\x20\x20\x20\x20\x20- .env\n"
 b"\x20\x20\x20\x20restart: unless-stopped\n"
 b"\x20\x20\x20\x20healthcheck:\n"
 b"\x20\x20\x20\x20\x20\x20test: [chr34CMDchr34,chr34pythonchr34,chr34-cchr34,chr34import urllib.request; urllib.request.urlopen(chr39http://localhost:8765/healthchr39)chr34]\n"
 b"\x20\x20\x20\x20\x20\x20interval: 30s\n"
 b"\x20\x20\x20\x20\x20\x20timeout: 5s\n"
 b"\x20\x20\x20\x20\x20\x20retries: 3\n"
 b"volumes:\n"
 b"\x20\x20sazabi_data:\n"
)
content = raw.decode("utf-8").replace("chr34 ", chr(34)).replace("chr34", chr(34)).replace("chr39", chr(39))
pathlib.Path(r"C:\Users\t.komurcu\sazabi\m2_storage\docker-compose.yml").write_text(content, "utf-8")
print(content)