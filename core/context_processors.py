import os


def currency_settings(request):
    currency = os.getenv('CURRENCY', 'USD')
    symbol = '$' if currency.upper() == 'USD' else 'ZK'
    return {'CURRENCY': currency.upper(), 'CURRENCY_SYMBOL': symbol}







