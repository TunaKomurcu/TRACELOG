import pathlib
dq=chr(34)
sq=chr(39)
nl=chr(10)
M2P=pathlib.Path(r'C:/Users/t.komurcu/SAZABI/m2_storage/tests/test_m2.py')
M4P=pathlib.Path(r'C:/Users/t.komurcu/SAZABI/m4_memory/tests/test_m4.py')
m2=M2P.read_text(encoding='utf-8')
m4=M4P.read_text(encoding='utf-8')
print('M2:',len(m2),'M4:',len(m4))
