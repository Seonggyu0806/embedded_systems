import board
import busio
import adafruit_ssd1306

i2c = busio.I2C(board.SCL, board.SDA)
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

temperature = 25.4   # 화면 배치 시험용 고정값 (센서 측정값 아님)
humidity = 61.2

display.fill(0)
display.text("Temperature", 0, 0, 1)
display.text(f"{temperature:.1f} C", 0, 16, 1)
display.text("Humidity", 0, 34, 1)
display.text(f"{humidity:.1f} %RH", 0, 50, 1)
display.show()

print("고정값 표시 완료")
