import pathlib
nl=chr(10)
sq=chr(39)
dq=chr(34)
lines=[
      dq+"version: 3.9"+dq,
      "",
      "services:",
        " storage:",
        " build: .",
        " ports:",
        " - "+dq+"8765:8765"+dq,
        " volumes:",
        " - sazabi_data:/data",
        " env_file:",
        " - .env",
        " restart: unless-stopped",
        " healthcheck:",
        " test: ["+dq+"CMD"+dq+", "+dq+"python"+dq+", "+dq+"-c"+dq+", "+dq+"import urllib.request; urllib.request.urlopen("+sq+"http://localhost:8765/health"+sq+")"+dq+"]",
        " interval: 30s",
        " timeout: 5s",
        " retries: 3",
        "",
        "volumes:",
        " sazabi_data:",
      ]
content=nl.join(lines)+nl
pathlib.Path(r"C:\Users\t.komurcu\sazabi\m2_storage\docker-compose.yml").write_text(content,"utf-8")
print("ok, lines=",len(lines))