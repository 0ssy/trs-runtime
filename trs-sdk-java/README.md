# trs-sdk-java

Java SDK for `trs-node` with API parity across TRS SDKs.

Methods:

- `health()`
- `submit(record)`
- `query(expr)`
- `sync(records)`
- `replay()`

## Run tests

```powershell
javac -d build\classes (Get-ChildItem -Recurse -File src\main\java\*.java).FullName (Get-ChildItem -Recurse -File tests\*.java).FullName
java -cp build\classes dev.trs.sdk.ClientTest
```
