import importlib
from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/ivr', methods=['GET', 'POST'])
def handle_ivr():
    # קליטת כל הפרמטרים מהמערכת (GET / POST)
    params = request.form.to_dict() if request.method == 'POST' else request.args.to_dict()

    # בדיקת הפרמטר - תומך גם ב-m וגם ב-module
    mod_number = params.get('m') or params.get('module')

    # בדיקה האם נשלח מספר תקין (ספרות בלבד)
    if not mod_number or not str(mod_number).strip().isdigit():
        return Response("id_list_message=t-שגיאה, לא הוגדר מספר מודול תקין", mimetype="text/plain; charset=utf-8")

    mod_number = str(mod_number).strip()
    file_name = f"mod_{mod_number}"  # למשל עבור 1 יחפש mod_1.py

    try:
        # טעינה אוטומטית של הקובץ המתאים לפי המספר
        target_module = importlib.import_module(f"modules.{file_name}")

        if hasattr(target_module, 'handle'):
            response_text = target_module.handle(params)
        else:
            response_text = f"id_list_message=t-שגיאה, בקובץ {file_name} חסרה פונקציית handle"

    except ModuleNotFoundError:
        # אם הוגדר מספר מודול שעדיין לא יצרת לו קובץ בגיטהאב
        response_text = f"id_list_message=t-מודול מספר {mod_number} אינו קיים במערכת"
    except Exception as e:
        print(f"Error in {file_name}: {e}")
        response_text = "id_list_message=t-אירעה שגיאה בשרת"

    # החזרת טקסט רגיל לימות המשיח
    return Response(str(response_text), mimetype="text/plain; charset=utf-8")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
