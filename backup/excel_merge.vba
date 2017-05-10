Sub merge()
    Dim MyPath, MyName, AWbName     'mypathÎªµ±Ç°Â·¾¶ mynameÎªÎÄ¼þÃû awbnameÎªµ±Ç°»î¶¯ÎÄ¼þÃû'
    Dim Wb As Workbook, WbN As String  'wb µ±Ç°Â·¾¶ÏÂÈ«²¿ÎÄ¼þÃûÊý×éÖÐµÄÎÄ¼þÃû'
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
                'next_row = .Range("A65536").End(xlUp).Row + 1
                next_row = .UsedRange.Rows.Count + Num
                .Cells(next_row, 1) = Left(MyName, Len(MyName) - 4)
                For G = 1 To Sheets.Count
                    next_row = .UsedRange.Rows.Count + 2
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
    MsgBox "¹²ºÏ²¢ÁË" & Num & "¸ö¹¤×÷±¡ÏÂµÄÈ«²¿¹¤×÷±í¡£ÈçÏÂ£º" & Chr(13) & WbN, vbInformation, "ÌáÊ¾"
End Sub
