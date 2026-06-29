import pathlib
p = pathlib.Path(r"C:\Users\t.komurcu\sazabi\m1_logger\logger.py")
s = p.read_text("utf-8")
s = s.replace("from datetime import datetime, timezone","from datetime import datetime, timezone"+chr(10)+"import forwarder",1)
old_write = chr(32)*16+"self._write_log(formatted)"
new_write = chr(32)*16+"self._write_log(formatted)"+chr(10)+chr(32)*16+"forwarder.forward_event(self.session_id,self._get_ts(formatted),stream_name,line)"
s = s.replace(old_write,new_write,1)
old_fmt = chr(32)*4+"def _format_line"
ts_method = chr(32)*4+"def _get_ts(self,line):"+chr(10)+chr(32)*8+"try: return line[1:line.index(chr(93))]"+chr(10)+chr(32)*8+"except Exception: return chr(34)+chr(34)"+chr(10)+chr(10)+chr(32)*4+"def _format_line"
s = s.replace(old_fmt,ts_method,1)
p.write_text(s,"utf-8")
print("patched len=",len(s))