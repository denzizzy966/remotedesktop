' ================================================================
'  LAN Remote Desktop Client - Silent VBScript Runner
'  Menjalankan client tanpa memunculkan jendela console/CMD sama sekali
' ================================================================
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' Pindah working directory ke direktori skrip
WshShell.CurrentDirectory = strDir

' Prioritas 1: Gunakan LANRemoteClient.exe jika ada
If FSO.FileExists(strDir & "\LANRemoteClient.exe") Then
    WshShell.Run """" & strDir & "\LANRemoteClient.exe""", 0, False
Else
    ' Prioritas 2: Gunakan pythonw.exe (Windowed Python tanpa jendela console)
    WshShell.Run "pythonw """ & strDir & "\client.py""", 0, False
End If
