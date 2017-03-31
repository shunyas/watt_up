void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.println("helow");
  randomSeed(analogRead(0));
}

void loop() {
  // put your main code here, to run repeatedly:
  float win = get_randf();
  float wout = get_randf();
  float eff = get_randf();
  float temp1 = get_randf();
  float temp2 = get_randf();

  Serial.print(win);
  Serial.print(",");
  Serial.print(wout);
  Serial.print(",");
  Serial.print(eff);
  Serial.print(",");
  Serial.print(temp1);
  Serial.print(",");
  Serial.println(temp2);

  delay(1000);
}

float get_randf(void){
  return (float)random(0,1000) / 1000;
}

