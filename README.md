# 12306
# 坐席类别
    # 特等座 P 选座只有A、C、F
    # 商务座 9 选座只有A、C、F
    # 一等座 M 选座为A、C、D、F
    # 二等座 O 选座为A、B、C、D、F（不是0，是大写的字母偶）

    # 高级动卧 A 不能选铺位
    # 高级软卧 6 不能选铺位
    # 一等卧 I 不能选铺位
    # 动卧 F 下铺 上铺
    # 二等卧 J 不能选铺位？

    # 硬座 1 不能选座
    # 软座 2 不能选座
    # 硬卧 3 下铺 中铺 上铺
    # 软卧 4 下铺 上铺
    
# 配置文件 config.properties
```
username=12306账号
password=12306密码
trainCode=订票车次（可多个车次，多个车次以英文逗号隔开，优先匹配前面的）
seatType=席别（上面坐席类别说明中）
date=车次日期，格式为yyyy-MM-dd，例如 2023-09-19）
from=出发站
to=到达站
passengers=乘客（可多个，名字以英文逗号隔开）
castNum=登录用户的身份证的后4位，获取短信验证码用
chooseSeats=选择动车/高铁坐席（高铁坐席一般为A、B、C, D、F，一人的话可以设置1F，1A等，两人的话为1D1F，或1F2F）
seatDetailType=卧铺（100为1个下铺，200为两个下铺，依次类推。101为1个下铺和上铺，211为2个下铺，一个中铺，一个上铺）
purpose_codes=（ADULT: 成人，0x00: 学生）
timesBetweenTwoQuery=两次查询的时间间隔（单位为秒），设置后自动查询余票（候补下单设置时默认会取消自动查询）
candidate=1（1为候补下单）
aftertime=12:00（只看几点以后的车次，仅当未设置订票车次时生效）
```
配置config.properties后，执行qr.py，resource目录下打开qr_image.jpg，手机12306 app扫码登录后，可自动购票。  

或执行login.py，通过账号密码方式自动登录后购票。

暂只支持单程票。

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
