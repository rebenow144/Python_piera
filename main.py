import csv
import serial
import datetime
import os
import logging
import time

# === CONFIGURATION ===
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200

# === Logging Setup ===
def setup_logging(log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')
    handler = logging.FileHandler(log_path)
    logging.getLogger().addHandler(handler)

# === CSV Utilities ===
def create_csv_filename(date_str):
    return f'PM_{date_str}.csv'

def write_csv_header_if_needed(file, headers):
    if not os.path.exists(file):
        with open(file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            print(f"[INFO] Header written to {file}")
    else:
        print(f"[INFO] Using existing file: {file}")

def write_to_csv(file, data_row):
    with open(file, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data_row)

# === สีตามระดับฝุ่น (พร้อมทศนิยม 2 ตำแหน่ง) ===
def color_pm_value(label, value):
    try:
        val = float(value)
        if val <= 12:
            color = "\033[92m"  # เขียว
            level = "ดี"
        elif val <= 35.4:
            color = "\033[93m"  # เหลือง
            level = "ปานกลาง"
        elif val <= 55.4:
            color = "\033[33m"  # ส้ม
            level = "เริ่มมีผล"
        elif val <= 150.4:
            color = "\033[91m"  # แดง
            level = "มีผลกระทบ"
        elif val <= 250.4:
            color = "\033[95m"  # ม่วง
            level = "อันตราย"
        else:
            color = "\033[41m"  # พื้นหลังแดง
            level = "อันตรายมาก"
        return f"{color}{label:<7}: {val:.2f} µg/m³ ({level})\033[0m"
    except:
        return f"{label:<7}: {value} µg/m³"

# === ฟังก์ชันเชื่อมต่อ Serial พร้อม Retry ===
def connect_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            print(f"[CONNECTED] Serial port {SERIAL_PORT} opened.")
            return ser
        except Exception as e:
            error_msg = f"[ERROR] Serial connection failed: {e}"
            logging.error(error_msg)
            print(error_msg)
            time.sleep(5)

# === Main Logic ===
def collect_data():
    log_path = os.path.join("logs", "pm_error_log.txt")
    setup_logging(log_path)

    # Flash drive functionality disabled
    # flash_drive_path = r'G:\\Endsave\\isp\\inroom'
    # if not os.path.exists(flash_drive_path):
    #     print(f"[WARNING] Flash drive not found. Using local path.")
    #     flash_drive_path = os.getcwd()

    all_keys = ['PC0.1', 'PC0.3', 'PC0.5', 'PC1.0', 'PC2.5', 'PC5.0', 'PC10',
                'PM0.1', 'PM0.3', 'PM0.5', 'PM1.0', 'PM2.5', 'PM5.0', 'PM10']
    headers = ["Date", "Time"] + all_keys
    current_date_str = datetime.datetime.now().strftime("%d-%m-%Y")

    # Flash drive file creation disabled
    # filename_flash = os.path.join(flash_drive_path, create_csv_filename(current_date_str))
    filename_local = os.path.join(os.getcwd(), create_csv_filename(current_date_str))

    # Flash drive header writing disabled
    # write_csv_header_if_needed(filename_flash, headers)
    write_csv_header_if_needed(filename_local, headers)

    ser = connect_serial()
    last_save_time_str = ""

    try:
        while True:
            try:
                line = ser.readline().decode('utf-8').strip()
                if not line:
                    continue

                if line.startswith("Dust Sensor Data:"):
                    line = line.split("Dust Sensor Data:")[1]

                values_raw = line.replace('\r', '').replace('\n', '').split(',')

                if len(values_raw) < 28:
                    continue

                keys = values_raw[::2]
                data_dict = dict(zip(keys, values_raw[1::2]))

                now = datetime.datetime.now()
                current_time_str = now.strftime('%H:%M:%S')

                if current_time_str == last_save_time_str:
                    continue
                last_save_time_str = current_time_str

                new_date_str = now.strftime("%d-%m-%Y")
                if new_date_str != current_date_str:
                    current_date_str = new_date_str
                    # Flash drive file update disabled
                    # filename_flash = os.path.join(flash_drive_path, create_csv_filename(current_date_str))
                    filename_local = os.path.join(os.getcwd(), create_csv_filename(current_date_str))
                    # Flash drive header writing disabled
                    # write_csv_header_if_needed(filename_flash, headers)
                    write_csv_header_if_needed(filename_local, headers)

                row = [now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S")]
                for key in all_keys:
                    row.append(data_dict.get(key, "0"))

                # Flash drive data writing disabled
                # write_to_csv(filename_flash, row)
                write_to_csv(filename_local, row)

                print("\n🌫️  Selected PM values:")
                for key in ['PC0.1', 'PC0.3', 'PC0.5', 'PC1.0', 'PC2.5', 'PC5.0', 'PC10',
                'PM0.1', 'PM0.3', 'PM0.5', 'PM1.0', 'PM2.5', 'PM5.0', 'PM10']:
                    print(color_pm_value(key, data_dict.get(key, '0')))
                print(f"✅ Saved at {row[1]}\n")

            except Exception as e:
                error_msg = f"Read error: {e}"
                logging.error(error_msg)
                print(error_msg)
                try:
                    ser.close()
                except:
                    pass
                print("[RETRYING] Reconnecting to serial port...")
                ser = connect_serial()

    except KeyboardInterrupt:
        print("\n👋 หยุดการทำงานแล้วโดยผู้ใช้ (Ctrl + C)")
        try:
            ser.close()
        except:
            pass

# === Entry Point ===
if __name__ == "__main__":
    collect_data()