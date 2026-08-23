import json

wk_strikes = [75,80,85,90,95,100,105,110,115,120,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,152.5,155,157.5,160,162.5,165,167.5,170,172.5,175,180,185,190,195,200,205,210,215,220,225,230,235]
mo_strikes = [70,75,80,85,90,95,100,105,110,115,120,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,152.5,155,157.5,160,165,170,175,180,185,190,195,200,205,210,215,220,225,230,235,240,245,250,255,260,265,270,280]

def codes(exp, strikes):
    out = []
    for s in strikes:
        n = int(round(s*1000))
        out.append(f"US.VST{exp}C{n}")
        out.append(f"US.VST{exp}P{n}")
    return out

wk = codes("260828", wk_strikes)
mo = codes("260918", mo_strikes)
json.dump(wk, open("C:/Users/Administrator/Desktop/stock/results/vst_week_codes.json","w"))
json.dump(mo, open("C:/Users/Administrator/Desktop/stock/results/vst_month_codes.json","w"))
print(f"week: {len(wk)}  codes")
print(f"month: {len(mo)}  codes")
print("week first5:", wk[:5])
print("week last5:", wk[-5:])
