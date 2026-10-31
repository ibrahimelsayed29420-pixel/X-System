import ollama

print("جاري استدعاء عقل X والاتصال بمحرك Ollama المحلي...")

try:
    response = ollama.chat(model='llama3.2', messages=[
      {
        'role': 'user',
        'content': 'مرحباً، عرّفني بنفسك بصفتك المساعد الذكي X وتحدث معي باللغة العربية باختصار شديد.',
      },
    ])
    
    print("\n--- رد النظام X ---")
    print(response['message']['content'])
    print("------------------")

except Exception as e:
    print(f"حدث خطأ أثناء الاتصال: {e}")