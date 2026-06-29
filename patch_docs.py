import pathlib
# spec.md
p = pathlib.Path(r"C:\Users\t.komurcu\sazabi\m3_compression\spec.md")
s = p.read_text("utf-8")
s = s.replace("Claude claude-haiku-4-5", "Google Gemini gemini-2.0-flash-lite")
s = s.replace("claude-haiku-4-5", "gemini-2.0-flash-lite")
s = s.replace("Claude API", "Gemini API")
p.write_text(s, "utf-8")
print("spec.md ok")
# pipeline.py
p2 = pathlib.Path(r"C:\Users\t.komurcu\sazabi\m3_compression\pipeline.py")
s2 = p2.read_text("utf-8")
s2 = s2.replace("Claude API", "Gemini API")
s2 = s2.replace("# Step 2: try LLM", "# Step 2: try Gemini LLM")
s2 = s2.replace("LLM compression failed", "Gemini compression failed")
p2.write_text(s2, "utf-8")
print("pipeline.py ok")