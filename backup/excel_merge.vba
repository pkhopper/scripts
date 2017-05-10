Sub merge()
    ' last row count is: .UsedRange.Rows.Count + .UsedRange.Row - 1
    ' ref: https://www.mrexcel.com/forum/excel-questions/693294-activesheet-usedrange-rows-count-returning-wrong-value.html
    Dim MyPath, MyName, AWbName
    Dim Wb As Workbook, WbN As String
    Dim G As Long
    Dim Num As Long
    Dim BOX As String
    Application.ScreenUpdating = False
    MyPath = ActiveWorkbook.Path
    MyName = Dir(MyPath & "\" & "*.xls")
    AWbName = ActiveWorkbook.Name
    
    Num = 0
    Do While MyName <> ""
        If MyName <> AWbName Then
            Set Wb = Workbooks.Open(MyPath & "\" & MyName)
            Num = Num + 1
            With Workbooks(1).ActiveSheet
                next_row = .UsedRange.Rows.Count + .UsedRange.Row
                .Cells(next_row, 1) = Left(MyName, Len(MyName) - 4)
                For G = 1 To Sheets.Count
                    next_row = .UsedRange.Rows.Count + .UsedRange.Row
                    Wb.Sheets(G).UsedRange.Copy .Cells(next_row, 1)
                Next
                WbN = WbN & Chr(13) & Wb.Name
                Wb.Close False
            End With
        End If
        MyName = Dir
    Loop
    Range("B1").Select
    Application.ScreenUpdating = True
    MsgBox "" & Num & "" & Chr(13) & WbN, vbInformation, ""
End Sub
