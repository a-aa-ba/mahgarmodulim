import requests

def handle(params):
    """
    מודול העברת/שיתוף קבצים בין מערכות ימות המשיח.
    תמיכה בפרמטרים קבועים P1 עד P8 לפי סדר השאלות.
    """

    # בדיקה האם הגענו מתוך השמעת קבצים (מהפרמטר what)
    is_playback = bool(params.get('what'))

    # ===========================================================
    # מצב א': הטמעה מתוך השמעת קבצים
    # ===========================================================
    if is_playback:
        # נתיב ושם הקובץ נלקחים ישירות מימות המשיח
        source_path = params.get('what')

        # שאלה 1: מספר מערכת מקור (P1, או ברירת מחדל ApiDID)
        source_did = params.get('P1') or params.get('source_did') or params.get('ApiDID', '')
        if not source_did:
            return "read=t-נא הקישו את מספר מערכת המקור=source_did,,10,7,Digits,no"

        # שאלה 2: סיסמת מערכת מקור (P2)
        source_token = params.get('source_token')
        if not source_token:
            source_pass = params.get('P2') or params.get('source_password')
            if not source_pass:
                return "read=t-נא הקישו את סיסמת הניהול של מערכת זו=source_password,,10,4,Digits,no"
            source_token = f"{source_did}:{source_pass}"

    # ===========================================================
    # מצב ב': שלוחה עצמאית (איסוף פרטי המקור לפי הסדר)
    # ===========================================================
    else:
        # שאלה 1: מספר מערכת מקור (P1)
        source_did = params.get('P1') or params.get('source_did') or params.get('ApiDID')
        if not source_did:
            return "read=t-נא הקישו את מספר מערכת המקור=source_did,,10,7,Digits,no"

        # שאלה 2: סיסמת מערכת מקור (P2)
        source_token = params.get('source_token')
        if not source_token:
            source_pass = params.get('P2') or params.get('source_password')
            if not source_pass:
                return "read=t-נא הקישו את סיסמת הניהול של מערכת המקור=source_password,,10,4,Digits,no"
            source_token = f"{source_did}:{source_pass}"

        # שאלה 3: שלוחת מקור (P3)
        source_folder = params.get('P3') or params.get('source_folder')
        if not source_folder:
            return "read=t-הקישו את שלוחת המקור. לשלוחה ראשית הקישו כוכבית וסולמית=source_folder,,10,1,Digits,no"

        # שאלה 4: שם/מספר קובץ מקור (P4)
        source_file = params.get('P4') or params.get('source_file')
        if not source_file:
            return "read=t-נא הקישו את מספר הקובץ שברצונכם לשתף, או כוכבית וארבע ספרות להודעת מערכת=source_file,,10,3,Digits,no"

        # הרכבת נתיב המקור
        source_file = source_file.strip()
        source_folder = source_folder.strip()
        is_source_root = source_folder in ('*', '*#', '0')

        if source_file.startswith('*'):
            src_filename = f"M{source_file[1:]}.wav"
        else:
            src_filename = f"{source_file}.wav"

        if is_source_root:
            source_path = f"ivr2:/{src_filename}"
        else:
            folder_clean = source_folder.replace('*', '/').strip('/')
            source_path = f"ivr2:/{folder_clean}/{src_filename}"

    # ===========================================================
    # איסוף פרטי מערכת היעד (משותף לשני המצבים לפי הסדר)
    # ===========================================================

    # שאלה 5: מספר מערכת יעד (P5)
    target_did = params.get('P5') or params.get('target_did')
    if not target_did:
        return "read=t-נא הקישו את מספר מערכת היעד=target_did,,10,7,Digits,no"

    # שאלה 6: סיסמת מערכת יעד (P6)
    target_pass = params.get('P6') or params.get('target_password')
    if not target_pass:
        return "read=t-נא הקישו את סיסמת הניהול של מערכת היעד=target_password,,10,4,Digits,no"

    target_token = f"{target_did}:{target_pass}"

    # שאלה 7: נתיב/שלוחה ביעד (P7)
    target_folder = params.get('P7') or params.get('target_folder')
    if not target_folder:
        return "read=t-הקישו את מספר שלוחת היעד. לשלוחה ראשית הקישו כוכבית וסולמית=target_folder,,10,1,Digits,no"

    # שאלה 8: שם הקובץ ביעד (P8)
    target_filename = None
    target_file = params.get('P8') or params.get('target_file')

    # אם אנחנו בהשמעת קבצים ולא נשלח מראש P8 / target_file, נותנים בחירה
    if is_playback and not target_file:
        keep_name = params.get('keep_name')
        if not keep_name:
            return "read=t-הקישו 1 לשמירה בשם הקובץ המקורי, או 2 להזנת שם קובץ חדש=keep_name,,1,1,Digits,no"
        
        if keep_name.strip() == '1':
            target_filename = source_path.split('/')[-1]

    # אם לא נבחר השם המקורי (או שנמצאים בשלוחה עצמאית), מוודאים שיש שם קובץ
    if not target_filename:
        if not target_file:
            return "read=t-הקישו את מספר הקובץ ביעד. להודעת מערכת הקישו כוכבית וארבע ספרות=target_file,,10,3,Digits,no"

        target_file = target_file.strip()
        if target_file.startswith('*'):
            msg_digits = target_file[1:]
            if len(msg_digits) != 4 or not msg_digits.isdigit():
                params.pop('target_file', None)
                params.pop('P8', None)
                return "read=t-שגיאה. להודעת מערכת יש להקיש כוכבית ולאחריה בדיוק ארבע ספרות=target_file,,10,3,Digits,no"
            target_filename = f"M{msg_digits}.wav"
        else:
            target_filename = f"{target_file}.wav"

    # הרכבת נתיב היעד
    target_folder = target_folder.strip()
    is_target_root = target_folder in ('*', '*#', '0')

    if is_target_root:
        target_path = f"ivr2:/{target_filename}"
    else:
        folder_clean = target_folder.replace('*', '/').strip('/')
        target_path = f"ivr2:/{folder_clean}/{target_filename}"

    # ===========================================================
    # ביצוע הורדה והעלאה
    # ===========================================================
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

    try:
        upload_url = "https://www.call2all.co.il/ym/api/UploadFile"
        up_params = {
            "token": target_token,
            "path": target_path,
            "convertAudio": "0"
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
            return "id_list_message=t-הקובץ הועבר בהצלחה למערכת היעד"
        else:
            print(f"Yemot Upload Error: {result_data}")
            return "id_list_message=t-שגיאה בהעלאת הקובץ. וודאו שמספר המערכת והסיסמה נכונים"

    except Exception as e:
        print(f"Error uploading file: {e}")
        return "id_list_message=t-אירעה שגיאה בשרת בהעלאת הקובץ ליעד"
