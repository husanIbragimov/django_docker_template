def mask_phone_number(phone_number):
    masked_phone_number = phone_number[:7] + "****" + phone_number[-3:]
    return masked_phone_number
