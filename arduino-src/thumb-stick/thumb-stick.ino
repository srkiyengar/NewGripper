int zeroX = 515;
int zeroY = 501;

//int zeroX = 0;
//int zeroY = 0;


void setup() {
  Serial.begin(9600);  
}


void loop() {

    int val, cmd;
    
    if (Serial.available()>0) {
      val = Serial.read();
 
      if (val == 0) {
        // Read joystick X - axis
        int x = analogRead(A0) - zeroX;
        Serial.println(x);
      }
      else if (val == 1) {
        // Read joystick Y - axis
        int y = analogRead(A1) - zeroY;
        Serial.println(y);
      }
      else if (val == 255) {
        // check and return button press
        int sel = !digitalRead(7);
        Serial.println(sel);
      }
      
    }
}


