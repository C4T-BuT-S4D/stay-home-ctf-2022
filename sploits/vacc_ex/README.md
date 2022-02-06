# STAY ~/ CTF 2022: VACCINATED EDITION

## vacc_ex

Author: [@jnovikov](https://github.com/jnovikov)

### Overview

The service is a kind of exchange/marketplace platform for new vaccines.

Users can register and create vaccine with private & public price. 

Other users can also buy the vaccine using the private/public ID.

### Vuln: NaN


1. Users can create vaccine stocks with any price they want except the [negative price](https://github.com/C4T-BuT-S4D/stay-home-ctf-2022/blob/master/services/vacc_ex/server/src/main/java/exchange/VaccineExchangeService.java#L70).
2. Users can buy the vaccine using the stored balance.
3. The validation functions do not check the 'special' float values like 'inf' or 'nan'. 
3. If you create the vaccine with NaN price it will pass all the check since the any comparisons with "NaN" value return False. 
4. The 'NaN' price will be subtracted from the user balance and also become 'NaN'.
5. You will be able to buy any product since (Nan < AnyValue) will return false.

Exploit: [nan_price.py](nan_price.py)

FIX:

Explicitly check the "NaN" value in the validatePrice function.
(Also you may want to replace already existed 'NaN' balances in Redis).

