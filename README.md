# 12306
# 坐席类别
    # 商务座 9
    # 一等座 M
    # 二等座 O（不是0，是大写的字母偶）

    # 高级软卧 6
    # 一等卧 I
    # 动卧 F
    # 二等卧 J

    # 硬座 1
    # 软座 2
    # 硬卧 3
    # 软卧 4
    
# 配置文件 config.properties
```
username=12306账号
password=12306密码
trainCode=订票车次
seatType=席别（上面坐席类别说明中的11种）
date=车次日期，格式为yyyy-MM-dd，例如 2023-09-19）
from=出发站
to=到达站
passengers=乘客
```
配置config.properties后，执行qr.py，resource目录下打开qr_image.jpg扫描登录后，自动购票

[//]: # (查询余票时，学生票purpose_codes为0x00，成人为ADULT)


passengerInfo_js.js中调用n()来获取encryptedData
```
    function n() {
        var x = "";
        try {
            x = window.json_ua.toString()
        } catch (y) {
            x = ""
        }
        return x
    }
```

suite1608722853171.js中获取encryptedData的大致流程

```
Wa - Os - je - Rc - Ac - hs - Ce - Q - gc(19) - Or(0) c981-- 循环 981 = c0 - Or(19)

Or(19) - ob - Be - $e - Ie - Oe - xe - Cs - Vc - mc - C - Xc - Kc - R - jc(0) - 981 = c3 - ba(1)

ba(1) - ab - Rs(0) - 981 = c4 --- c979 > c974.length - Sa(0)

Sa(0) - Qc - Ze(0) - 981-- Rs(6)

Ze(11) - Ks - Nc - k(0) 14 c981 = c9 - k(15)判断c981 是否大于0 981 == 0时Sr(10)  19 - vc(0)

vc(0) - Hc - Se - rb - Sr(0) 9 981-- k(15)

Sr(10) - se(0) - Ja(0) - Z - fs - ua - fa(17) - ma(0) - Oc - Ls(2) c981-- fa(0) ---循环（ma, Oc, Ls)

fa(6) -- c981.length == 0时Ls(3)

Ls(3) - W(0) - la - ks - Ge - Ys - ja
```
