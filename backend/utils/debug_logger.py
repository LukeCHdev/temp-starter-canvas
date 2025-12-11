import json
import traceback

def debug_log(label: str, data: any):
    print("\n" + "="*100)
    print(f"🔍 DEBUG: {label}")
    print("-"*100)

    try:
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(str(data))
    except Exception as e:
        print(f"⚠️ Error printing log: {str(e)}")

    print("="*100 + "\n")
