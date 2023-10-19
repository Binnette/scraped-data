def parse_opening_hours(opening_hours):
    if len(opening_hours) == 0:
        return ""
    days = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
    day_hours = [None]*7
    for i in range(1, 8):
        index = i % 7
        if opening_hours[index]:
            day_hours[i-1] = f"{opening_hours[index][0]['start_time']}-{opening_hours[index][0]['end_time']}"

    groups = []
    cur_group = None
    for i in range(0, 7):
        h = day_hours[i]
        if h == None:
            if cur_group:
                groups.append(cur_group)
                cur_group = None
            continue
        if cur_group == None:
            cur_group = {
                "hours": h,
                "min_day": i,
                "max_day": i
            }
        elif cur_group["hours"] == h:
            cur_group["max_day"] = max(cur_group["max_day"], i)    
        else:
            groups.append(cur_group)
            cur_group = {
                "hours": h,
                "min_day": i,
                "max_day": i
            }
    if cur_group:
        groups.append(cur_group)

    result = []
    if len(groups) == 0:
        return ""
    if len(groups) == 1 and groups[0]["min_day"] == 0 and groups[0]["max_day"] == 6:
        return groups[0]["hours"]

    for group in groups:
        if group["min_day"] == group["max_day"]:
            day = group["min_day"]
            result.append(f"{days[(day+1)%7]} {group["hours"]}")
        else:
            min_day = group["min_day"]
            max_day = group["max_day"]
            result.append(f"{days[(min_day+1)%7]}-{days[(max_day+1)%7]} {group["hours"]}")

    return ';'.join(result)


# Write tests for different cases

a1 = parse_opening_hours([[],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[]])
a2 = "Mo-Fr 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[],[ { "start_time": "08:30", "end_time": "18:00" }],[],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "23:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[]])
a2 = "Mo 08:30-18:00;We 08:30-18:00;Th 08:30-23:00;Fr 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[],[ { "start_time": "08:30", "end_time": "18:00" }],[],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[]])
a2 = "Mo 08:30-18:00;We-Fr 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[],[ { "start_time": "08:30", "end_time": "18:00" }],[{ "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[]])
a2 = "Mo-Fr 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[],[ { "start_time": "08:30", "end_time": "18:00" }],[{ "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[{"start_time": "08:30", "end_time": "18:00"}]])
a2 = "Mo-Sa 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[{"start_time":"08:30", "end_time":"18:00"}], [{"start_time":"08:30", "end_time":"18:00"}], [{"start_time":"08:30", "end_time":"18:00"}], [{"start_time":"08:30", "end_time":"18:00"}], [{"start_time":"08:30", "end_time":"18:00"}], [{"start_time":"08:30", "end_time":"18:00"}], [{"start_time":"08:30", "end_time":"18:00"}]])
a2 = "08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[{ "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[ { "start_time": "08:30", "end_time": "18:00" }],[{"start_time": "08:30", "end_time": "18:00" }]])
a2 = "Mo 08:30-18:00;We-Su 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[{ "start_time": "08:30", "end_time": "18:00" }],[],[{ "start_time": "08:30", "end_time": "18:00" }],[{ "start_time": "08:30", "end_time": "18:00" }],[{ "start_time": "08:30", "end_time": "18:00" }],[{ "start_time": "08:30", "end_time": "18:00" }],[{"start_time": "08:30", "end_time": "18:00"}]])
a2 = "Tu-Su 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([ [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }] ])
a2 = "06:00-22:00"
assert a1 == a2

a1 = parse_opening_hours([ [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }], [], [{ "start_time": "06:00", "end_time": "22:00" }], [{ "start_time": "06:00", "end_time": "22:00" }] ])
a2 = "Mo-We 06:00-22:00;Fr-Su 06:00-22:00"
assert a1 == a2

a1 = parse_opening_hours([[{"start_time":"08:30","end_time":"12:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"18:00"}],[{"start_time":"08:30","end_time":"12:00"}]])
a2 = "Mo-Fr 08:30-18:00;Sa-Su 08:30-12:00"
assert a1 == a2

a1 = parse_opening_hours([[],[{"start_time":"08:30","end_time":"18:00"}],[],[],[],[],[]])
a2 = "Mo 08:30-18:00"
assert a1 == a2

a1 = parse_opening_hours([[],[{"start_time":"08:30","end_time":"18:00"}],[],[{"start_time":"08:30","end_time":"18:00"}],[],[],[]])
a2 = 'Mo 08:30-18:00;We 08:30-18:00'
assert a1 == a2

a1 = parse_opening_hours([[],[],[],[],[],[],[]])
a2 = ''
assert a1 == a2

a1 = parse_opening_hours([])
a2 = ''
assert a1 == a2

print("All tests passed!")