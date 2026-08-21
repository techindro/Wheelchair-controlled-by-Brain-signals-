import serial
import serial.tools.list_ports
import socket
import threading
import sys

UDP_IP = "127.0.0.1"
UDP_PORT = 6868
BAUDRATE = 9600

COMMANDS = {
    'f': 'Forward',
    'b': 'Backward',
    'l': 'Turn Left',
    'r': 'Turn Right',
    's': 'Stop',
    '1': 'Gear 1 (120 PWM)',
    '2': 'Gear 2 (180 PWM)',
    '3': 'Gear 3 (255 PWM)'
}

def connect_serial():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if not ports:
        print("[!] No serial port detected. Running UDP monitor.")
        return None
    
    port = ports[0]
    try:
        ser = serial.Serial(port, BAUDRATE, timeout=1)
        print(f"[+] Connected to {port} @ {BAUDRATE} baud")
        return ser
    except Exception as e:
        print(f"[!] Failed to open {port}: {e}")
        return None

def voice_listener(ser):
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        mic = sr.Microphone()
        voice_map = {'forward': 'f', 'back': 'b', 'left': 'l', 'right': 'r', 'stop': 's'}

        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1)

        while True:
            with mic as source:
                audio = r.listen(source, phrase_time_limit=3)
            try:
                text = r.recognize_google(audio).lower()
                for word, cmd in voice_map.items():
                    if word in text:
                        print(f"[Voice] {word} -> '{cmd}'")
                        if ser and ser.is_open:
                            ser.write(cmd.encode('utf-8'))
                        break
            except Exception:
                pass
    except ImportError:
        pass

def main():
    ser = connect_serial()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"[+] UDP server listening on {UDP_IP}:{UDP_PORT}")

    t = threading.Thread(target=voice_listener, args=(ser,), daemon=True)
    t.start()

    try:
        while True:
            data, _ = sock.recvfrom(1024)
            cmd = data.decode('utf-8', errors='ignore').strip()
            if cmd in COMMANDS:
                print(f"[EEG] '{cmd}' ({COMMANDS[cmd]})")
                if ser and ser.is_open:
                    ser.write(cmd.encode('utf-8'))
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if ser and ser.is_open:
            ser.close()
        sock.close()

if __name__ == '__main__':
    main()
