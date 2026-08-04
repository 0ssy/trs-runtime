# trs-sdk-kotlin

Kotlin SDK for `trs-node` with API parity across TRS SDKs.

Methods:

- `health()`
- `submit(record)`
- `query(expr)`
- `sync(records)`
- `replay()`

## Run tests

```powershell
$kotlin = "$env:USERPROFILE\.kotlin\kotlinc\bin\kotlinc.bat"
Set-Location .\trs-sdk-kotlin
& $kotlin .\src\main\kotlin\dev\trs\sdk\*.kt .\tests\ClientTest.kt -include-runtime -d .\build\tests.jar
java -jar .\build\tests.jar
```
