import importlib
import re
from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/ivr', methods=['GET', 'POST'])
def handle_ivr():
    # קבלת כל הנתונים שנשלחו (תומך גם ב-GET וגם ב-POST)
    if request.method == 'POST':
        params = request.form.to_dict()
    else:
        params = request.args.to_dict()

    # חילוץ שם המודול מתוך הפרמטר module
    module_name = params.get('module', '').strip()

    # בדיקת תקינות כדי למנוע ניסיונות גישה לקבצים מחוץ לתיקייה
    if not module_name or not re.match(r'^[a-zA-Z0-9_]+$', module_name):
        return Response("id_list_message=t-שגיאה לא נשלח שם מודול תקין", mimetype="text/plain; charset=utf-8")

    try:
        # טעינה דינמית של הקובץ מתוך תיקיית modules
        # לדוגמה: אם נשלח module=quiz, הוא יטען את הקובץ modules/quiz.py
        target_module = importlib.import_module(f"modules.{module_name}")

        # הפעלת פונקציית handle מתוך קובץ המודול
        if hasattr(target_module, 'handle'):
            response_text = target_module.handle(params)
        else:
            response_text = f"id_list_message=t-בקובץ המודול {module_name} חסרה פונקציית handle"

    except ModuleNotFoundError:
        # במקרה שנשלח שם מודול שאינו קיים בתיקייה
        response_text = f"id_list_message=t-המודול {module_name} לא נמצא במערכת"
    except Exception as e:
        # הדפסת השגיאה בלוגים של רנדר
        print(f"שגיאה בהפעלת מודול {module_name}: {e}")
        response_text = "id_list_message=t-אירעה שגיאה בשרת בהפעלת המודול"

    # החזרת התשובה כטקסט פשוט בקידוד UTF-8 כפי שדורשת ימות המשיח
    return Response(str(response_text), mimetype="text/plain; charset=utf-8")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
