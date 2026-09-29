import requests

def handle(params):
    """
    מודול 1: העברת/שיתוף קבצים בין מערכות ימות המשיח
    מצב 1: הזנה ידנית של קובץ המקור
    מצב 2: שליחה מתוך שלוחת השמעת קבצים (נשלח פרמטר what)
    """

    # -----------------------------------------------------------
    # שלב 1: זיהוי קובץ המקור
    # -----------------------------------------------------------
    source_path = params.get('what')  # נשלח אוטומטית במצב של השמעת קבצים

    if not source_path:
        # מצב 1: המאזין צריך להזין את מספר הקובץ במערכת הנוכחית
        source_file = params.get('source_file')
        if not source_file:
            return "read=t-נא הקישו את מספר הקובץ שברצונכם לשתף, או כוכבית וארבע ספרות להודעת מערכת=source_file,,10,3,Digits,no"
        
        # פענוח הקובץ שנבחר
        source_file = source_file.strip()
        if source_file.startswith('*'):
            source_path = f"ivr2:/messages/M{source_file[1:]}.wav"
        else:
            source_folder = params.get('source_folder', '1').strip('/')
            source_path = f"ivr2:/{source_folder}/{source_file}.wav"

    # -----------------------------------------------------------
    # שלב 2: השגת טוקן/סיסמה למערכת המקור
    # -----------------------------------------------------------
    # אם הגדרת מראש בהגדרות השלוחה source_token, נשתמש בו ישירות.
    # אם לא, נבקש מהמאזין את סיסמת הניהול של המערכת הנוכחית.
    source_token = params.get('source_token')
    if not source_token:
        source_pass = params.get('source_password')
        if not source_pass:
            return "read=t-נא הקישו את סיסמת הניהול של מערכת זו=source_password,,10,4,Digits,no"
        source_did = params.get('ApiDID', '')
        source_token = f"{source_did}:{source_pass}"

    # -----------------------------------------------------------
    # שלב 3: בקשת פרטי מערכת היעד
    # -----------------------------------------------------------
    target_did = params.get('target_did')
    if not target_did:
        return "read=t-נא הקישו את מספר מערכת היעד=target_did,,10,7,Digits,no"

    target_pass = params.get('target_password')
    if not target_pass:
        return "read=t-נא הקישו את סיסמת הניהול של מערכת היעד=target_password,,10,4,Digits,no"

    # -----------------------------------------------------------
    # שלב 4: בקשת מספר הקובץ ביעד (* = הודעת מערכת M)
    # -----------------------------------------------------------
    target_file = params.get('target_file')
    if not target_file:
        return "read=t-הקישו את מספר הקובץ ביעד. להודעת מערכת הקישו כוכבית וארבע ספרות=target_file,,10,3,Digits,no"

    target_file = target_file.strip()

    # בדיקת תקינות הקשה: אם מתחיל ב-* חובה 4 ספרות אחריו
    if target_file.startswith('*'):
        msg_digits = target_file[1:]
        if len(msg_digits) != 4 or not msg_digits.isdigit():
            # מחיקת ההקשה השגויה ובקשה מחדש
            params.pop('target_file', None)
            return "read=t-שגיאה. להודעת מערכת יש להקיש כוכבית ולאחריה בדיוק ארבע ספרות=target_file,,10,3,Digits,no"
        target_path = f"ivr2:/messages/M{msg_digits}.wav"
    else:
        # קובץ רגיל בשלוחה (ברירת מחדל שלוחה 1, ניתן לקבוע ב-target_folder)
        target_folder = params.get('target_folder', '1').strip('/')
        target_path = f"ivr2:/{target_folder}/{target_file}.wav"

    target_token = f"{target_did}:{target_pass}"

    # -----------------------------------------------------------
    # שלב 5: ביצוע ההורדה ממערכת המקור
    # -----------------------------------------------------------
    try:
        download_url = "https://www.call2all.co.il/ym/api/DownloadFile"
        down_res = requests.get(
            download_url,
            params={"token": source_token, "path": source_path},
            timeout=30
        )

        if down_res.status_code != 200 or not down_res.content:
            return "id_list_message=t-שגיאה, הקובץ לא נמצא במערכת המקור או שפרטי הגישה שגויים"
    except Exception as e:
        print(f"Error downloading file: {e}")
        return "id_list_message=t-אירעה שגיאת תקשורת בהורדת הקובץ"

    # -----------------------------------------------------------
    # שלב 6: העלאת הקובץ למערכת היעד
    # -----------------------------------------------------------
    try:
        upload_url = "https://www.call2all.co.il/ym/api/UploadFile"
        up_params = {
            "token": target_token,
            "path": target_path,
            "convertAudio": "0"  # הקובץ כבר בפורמט תואם, אין צורך בהמרה
        }
        files = {
            "file": ("audio.wav", down_res.content, "audio/wav")
        }

        up_res = requests.post(
            upload_url,
            params=up_params,
            files=files,
            timeout=60
        )

        result_data = up_res.json()
        if result_data.get('responseStatus') == 'OK':
            # הצלחה!
            return "id_list_message=t-הקובץ הועבר בהצלחה למערכת היעד"
        else:
            print(f"Yemot Upload Error: {result_data}")
            return "id_list_message=t-שגיאה בהעלאת הקובץ. וודאו שמספר המערכת והסיסמה נכונים"

    except Exception as e:
        print(f"Error uploading file: {e}")
        return "id_list_message=t-אירעה שגיאה בשרת בהעלאת הקובץ ליעד"
