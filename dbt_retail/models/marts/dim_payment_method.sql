select
    {{ surrogate_key(['payment_method']) }} as payment_method_key,
    payment_method,
    case
        when payment_method = 'CASH' then 'CASH'
        when payment_method = 'CARD' then 'CARD'
        else 'DIGITAL_WALLET'
    end as payment_type
from (
    select column1 as payment_method
    from values ('CASH'), ('CARD'), ('ESEWA'), ('KHALTI'), ('FONEPAY')
)