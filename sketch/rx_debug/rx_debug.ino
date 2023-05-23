
#include <lmic.h>
#include <hal/hal.h>
#include <arduino_lmic_hal_boards.h>

#include <SPI.h>

#include <stdarg.h>
#include <stdio.h>

// we formerly would check this configuration; but now there is a flag,
// in the LMIC, LMIC.noRXIQinversion;
// if we set that during init, we get the same effect.  If
// DISABLE_INVERT_IQ_ON_RX is defined, it means that LMIC.noRXIQinversion is
// treated as always set.
//
// #if !defined(DISABLE_INVERT_IQ_ON_RX)
// #error This example requires DISABLE_INVERT_IQ_ON_RX to be set. Update \
//        lmic_project_config.h in arduino-lmic/project_config to set it.
// #endif

// How often to send a packet. Note that this sketch bypasses the normal
// LMIC duty cycle limiting, so when you change anything in this sketch
// (payload length, frequency, spreading factor), be sure to check if
// this interval should not also be increased.
// See this spreadsheet for an easy airtime and duty cycle calculator:
// https://docs.google.com/spreadsheets/d/1voGAtQAjC1qBmaVuP1ApNKs1ekgUjavHuVQIXyYSvNc

#define NODE_IDX 42
#define RSSI_RESET_VAL 128
#define SCHEDULE_LEN 10
#define FREQ_EXPT 915000000
#define FREQ_CNFG 917000000
#define RB_LEN 65

// Pin mapping
const lmic_pinmap lmic_pins = {
  .nss = D10,
  .rxtx = LMIC_UNUSED_PIN,
  .rst = A0,
  .dio = {2, 3, 4},
};


// These callbacks are only used in over-the-air activation, so they are
// left empty here (we cannot leave them out completely unless
// DISABLE_JOIN is set in arduino-lmoc/project_config/lmic_project_config.h,
// otherwise the linker will complain).
void os_getArtEui (u1_t* buf) { }
void os_getDevEui (u1_t* buf) { }
void os_getDevKey (u1_t* buf) { }

// this gets callled by the library but we choose not to display any info;
// and no action is required.
void onEvent (ev_t ev) {
}


osjob_t arbiter_job;
osjob_t loop_job;
osjob_t timeoutjob;
static void tx_func (osjob_t* job);

// WCSNG

// Serial Buffer(s)
byte buf_in[4];
byte buf_out[4];
byte buf_tx[16];
// 0: tx_interval_global (ms)
// 1: packet_size_bytes
// 2: Experiment Time in seconds
// 3: Experiment Time Multiplier
// 4: Enable CAD
// 5: DIFS as number of CADs
// 6: Backoff CFG1 - Backoff Unit Length in ms
// 7: Backoff CFG2 - Max backoff multiplier
// 8: tx_interval_multiplier
// 9: scheduler_interval_mode (0: Periodic, 1: Poisson, 2: Periodic with Variance);
//---------------------------------
// 10: Result - Counter Byte 0
// 11: Result - Counter Byte 1
// 12: Result - Counter Byte 2
// 13: Result - Backoff Counter Byte 0
// 14: Result - Backoff Counter Byte 1
// 15: Result - Backoff Counter Byte 2
//---------------------------------

// 17: {4bits txsf, 4bits rxsf}
// 18: {4bits txbw, 4bits rxbw}
// 19: {4bits txcr, 4bits txcr}
// 20: CAD Config Register {bit 0: Fixed DIFS Size, bit 1: LMAC CSMA}
// 21: Listen before talk ticks (x16) 
// 22: Listen before talk max RSSI s1_t
// 23: Kill CAD Wait time (0 or 1)
//---------------------------------
//24--44 - Node Idx
//---------------------------------
// 45: periodic_tx_variance (x10 ms)

// 46: Result - LBT Counter Byte 0
// 47: Result - LBT Counter Byte 1
// 48: Result - LBT Counter Byte 2

// For Ref
//enum _cr_t { CR_4_5=0, CR_4_6, CR_4_7, CR_4_8 };
//enum _sf_t { FSK=0, SF7, SF8, SF9, SF10, SF11, SF12, SFrfu };
//enum _bw_t { BW125=0, BW250, BW500, BWrfu };

byte reg_array[64];
ostime_t interarrival_array[2048];
u4_t interarrival_ind;
ostime_t expt_start_time, expt_stop_time; // 1ms is 62.5 os ticks
int arbiter_state;
u4_t scheduler_list_ms[SCHEDULE_LEN];

u1_t freq_expt_ind, freq_cnfg_ind;
u4_t trx_freq_vec[24];

u4_t multi_tx_packet_ctr;
u4_t global_cad_counter;
u4_t global_lbt_counter;
//


// Enable rx mode and call func when a packet is received
void rx(osjobcb_t func) {
  LMIC.osjob.func = func;
  LMIC.rxtime = os_getTime(); // RX _now_
  // Enable "continuous" RX (e.g. without a timeout, still stops after
  // receiving a packet)

  os_radio(RADIO_RXON);
}



static void rxdone_func (osjob_t* job) {
   // Blink once to confirm reception and then keep the led on
  digitalWrite(LED_BUILTIN, LOW); // off
  delay(1);
  digitalWrite(LED_BUILTIN, HIGH); // on

  buf_in[0] = LMIC.frame[0];
  buf_in[1] = LMIC.frame[1];
  buf_in[2] = LMIC.frame[2];
  buf_in[3] = LMIC.frame[3];

  Serial.print("[");
  Serial.print(buf_in[0]);
  Serial.print(",");
  Serial.print(buf_in[1]);
  Serial.print(",");
  Serial.print(buf_in[2]);
  Serial.print(",");
  Serial.print(buf_in[3]);
  Serial.print("]");
  Serial.print(";");
  
  Serial.print("RSSI: ");
  Serial.print(LMIC.rssi);
  Serial.print("; ");

  Serial.print("CRC: ");
  Serial.print(LMIC.sysname_crc_err);
  Serial.print("\n");
  
  // Arbiter
  os_setCallback(job, rx_func);
  
}

static void rx_func (osjob_t* job) {
  // GET BUF_OUT
  rx(rxdone_func);
}

static byte get_nth_byte(int number_in, byte idx){
  return (number_in>>(idx*8));
}


// application entry point
void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  // initialize runtime env
  os_init();

  // disable RX IQ inversion
  LMIC.noRXIQinversion = true;
  
  LMIC.rps = MAKERPS(SF8 , BW125, CR_4_8, 0, 0); // WCSNG
  LMIC.sysname_tx_rps =  MAKERPS(SF8 , BW125, CR_4_8, 0, 0); // WCSNG
  LMIC.sysname_cad_rps =  MAKERPS(SF8 , BW125, CR_4_8, 0, 0); // WCSNG
  LMIC.txpow = 21;
  LMIC.radio_txpow = 21; // WCSNG



  // Set the generic TRX frequencies:
  for(byte idx = 0;idx<24;idx++){
      trx_freq_vec[idx] = 904000000 + ((u4_t)idx) * 1000000;
  }

  freq_expt_ind = 16;
  freq_cnfg_ind = 18; // 13
  // Set the LMIC CAD Frequencies
  LMIC.freq = trx_freq_vec[freq_cnfg_ind]; // WCSNG
  LMIC.sysname_cad_freq_vec[0] = trx_freq_vec[freq_expt_ind];
  LMIC.sysname_cad_freq_vec[1] = trx_freq_vec[freq_expt_ind]-1000000;
  LMIC.sysname_cad_freq_vec[2] = trx_freq_vec[freq_expt_ind]-2000000;
  LMIC.sysname_cad_freq_vec[3] = trx_freq_vec[freq_expt_ind]-4000000;
  

  Serial.flush();

  // Setup Registers
  interarrival_ind = 0;
  arbiter_state = 0; // Resting state
  multi_tx_packet_ctr = 0; // Resetting counter
  
  reg_array[0] = 90;     // tx_interval
  reg_array[1] = 16;     // Packet Size Bytes
  reg_array[2] = 10;     // Experiment run length in seconds
  reg_array[3] = 1;      // Time multiplier for expt time
  reg_array[4] = 0;      // Enable CAD - OFF by default
  reg_array[5] = 8;      // DIFS as number of CADs
  reg_array[6] = 12;     // Backoff Unit in ms (backoff cnfg 1)
  reg_array[7] = 4;      // Max Backoff Unit Multiplier length (backoff cnfg 2)
  reg_array[8] = 1;      // tx_interval_multiplier
  reg_array[9] = 0;      // scheduler_interval_mode (0: Periodic, 1: Poisson, 2: Periodic with Variance);

  reg_array[17] = 34; // 17: {4bits txsf, 4bits rxsf}
  reg_array[18] = 34; // 18: {4bits txbw, 4bits rxbw}
  reg_array[19] = 51; // 19: {4bits txcr, 4bits txcr}

  reg_array[20] = 0;      // CAD Type and Config Reg
  reg_array[21] = 0;      // Listen before talk ticks (x16) 
  reg_array[22] = -90;    // Listen before talk max RSSI s1_t
  reg_array[23] = 1;      // Kill CAD Wait time (0 or 1)

  reg_array[45] = 10;    // Variance if using periodic scheduling

//
  LMIC.sysname_kill_cad_delay  = 1; // Kill CAD Wait time (0 or 1)
//

  // SPAM CONFIG
  LMIC.dataLen = 16;
  for(int i = 0; i<LMIC.dataLen; i++)
    LMIC.frame[i] = 0;

  //

  for(byte idx = 0;idx<20;idx++)
    reg_array[24+idx] = RSSI_RESET_VAL;

  buf_in[0] == 0;
  buf_in[1] == 0;
  buf_in[2] == 0;

  // Say Hi
  Serial.print("Hi I am Node ");
  Serial.print(NODE_IDX);
  Serial.print("\n");

  // setup initial job
  expt_start_time = os_getTime();
  expt_stop_time = expt_start_time + ms2osticks(reg_array[2]*reg_array[3]*1000);
  os_setCallback(&arbiter_job, rx_func);

}

void loop() {
  // execute scheduled jobs and events
  os_runloop_once();
}


//float sum_var = 0;
//float ind_var = 1;
//trash:
//  u4_t rand_var = get_wait_time_ms();
//  sum_var += rand_var;
//  Serial.print(ind_var);
//  Serial.print(": ");
//  Serial.print(rand_var);
//  Serial.print(", ");
//  Serial.print(sum_var/ind_var);
//  Serial.print("\n");
////  delay(10);
//  ind_var++;
