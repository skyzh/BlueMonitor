# BlueMonitor

Running on Raspberry Pi, this program can send sensor data to Firebase

## Data Packet

```
|                    Header               | Payload |    Ending    |
| Message ID | Response ID |  Command ID  |         | Verification |
|      2     |      2      |      2       |    8    |       2      |

(16 bytes)
```

BlueSensor will send a packet with 128 bits of 0 to Raspberry Pi every 1 second.
