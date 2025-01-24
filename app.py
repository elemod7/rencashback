import io
import base64
import matplotlib.pyplot as plt

from flask import Flask, render_template, request

app = Flask(__name__)

DEPOSIT_RATES = [21.6, 18.5, 12.5, 8, 5]
TAX_DEDUCTIONS = {13: 19500, 15: 22500, 18: 27000, 20: 30000, 22: 33000}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            annual_nsz_payment = float(request.form.get('annual_nsz_payment', 0))
            deposit_amount = float(request.form.get('deposit_amount', 0))
            tax_rate = int(request.form.get('tax_rate', 0))
            has_official_income = 'has_official_income' in request.form

            if annual_nsz_payment < 300000:
                return render_template('index.html', error="Сумма ежегодного взноса по НСЖ должна быть не менее 300 000 руб.")
            if tax_rate not in TAX_DEDUCTIONS:
                return render_template('index.html', error="Выберите корректную ставку налога из списка [13, 15, 18, 20, 22].")

            tax_rate_decimal = tax_rate / 100

            if 300000 <= annual_nsz_payment < 500000:
                nsz_cashback_rate = 0.34
            else:
                nsz_cashback_rate = 0.36

            total_initial_amount = deposit_amount + annual_nsz_payment
            deposit_only_amount = deposit_amount + annual_nsz_payment

            deposit_only_income = [] 
            for rate in DEPOSIT_RATES:
                annual_income = deposit_only_amount * (rate / 100) 
                net_income = annual_income * (1 - tax_rate_decimal) 
                deposit_only_income.append(net_income)

            total_deposit_only_income = sum(deposit_only_income)
            final_deposit_only_balance = deposit_only_amount + total_deposit_only_income

            deposit_split_income = []
            nsz_cashback_income = [] 
            nsz_tax_deduction_income = [] 

            for rate in DEPOSIT_RATES:
                deposit_income = deposit_amount * (rate / 100)
                net_deposit_income = deposit_income * (1 - tax_rate_decimal)
                deposit_split_income.append(net_deposit_income)
                nsz_cashback = annual_nsz_payment * nsz_cashback_rate
                nsz_net_cashback = nsz_cashback * (1 - tax_rate_decimal)
                nsz_cashback_income.append(nsz_net_cashback)
                nsz_tax_deduction = TAX_DEDUCTIONS[tax_rate] * 2 if has_official_income else 0
                nsz_tax_deduction_income.append(nsz_tax_deduction)

            total_deposit_split_income = sum(deposit_split_income)
            total_nsz_cashback_income = sum(nsz_cashback_income)
            total_nsz_tax_deduction_income = sum(nsz_tax_deduction_income)

            total_combined_split_income = (
                total_deposit_split_income
                + total_nsz_cashback_income
                + total_nsz_tax_deduction_income
            )

            final_combined_split_balance = (
                deposit_amount
                + annual_nsz_payment
                + total_combined_split_income
            )

            difference = final_combined_split_balance - final_deposit_only_balance

            years = list(range(1, len(DEPOSIT_RATES) + 1))
            plt.figure(figsize=(10, 6))

            deposit_balances_by_year = []
            for i in range(len(deposit_only_income)):
                balance_i = deposit_only_amount + sum(deposit_only_income[:i+1])
                deposit_balances_by_year.append(balance_i)

            plt.plot(years, deposit_balances_by_year, label="Вклад (вся сумма)")

            combined_balances_by_year = []
            for i in range(len(deposit_split_income)):
                balance_i = (
                    deposit_amount
                    + annual_nsz_payment
                    + sum(deposit_split_income[:i+1])
                    + sum(nsz_cashback_income[:i+1])
                    + sum(nsz_tax_deduction_income[:i+1])
                )
                combined_balances_by_year.append(balance_i)

            plt.plot(years, combined_balances_by_year, label="Вклад + НСЖ")
            plt.xlabel("Годы")
            plt.ylabel("Сумма, руб.")
            plt.title("Сравнение роста суммы без капитализации")
            plt.legend()
            plt.grid()
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            graph_url = base64.b64encode(img.getvalue()).decode()
            plt.close()

            print("==== ОТЛАДКА ====")
            print("deposit_only_amount (на вклад):", deposit_only_amount)
            print("deposit_only_income:", deposit_only_income)
            print("total_deposit_only_income:", total_deposit_only_income)
            print("final_deposit_only_balance:", final_deposit_only_balance)
            print("---")
            print("deposit_split_income:", deposit_split_income)
            print("nsz_cashback_income:", nsz_cashback_income)
            print("nsz_tax_deduction_income:", nsz_tax_deduction_income)
            print("total_combined_split_income:", total_combined_split_income)
            print("final_combined_split_balance:", final_combined_split_balance)
            print("difference:", difference)

            return render_template(
                'result.html',
                deposit_only_income=deposit_only_income,
                total_deposit_only_income=total_deposit_only_income,
                final_deposit_only_balance=final_deposit_only_balance,
                deposit_split_income=deposit_split_income,
                nsz_cashback_income=nsz_cashback_income,
                nsz_tax_deduction_income=nsz_tax_deduction_income,
                total_combined_split_income=total_combined_split_income,
                final_combined_split_balance=final_combined_split_balance,
                difference=difference,
                graph_url=graph_url,
                zip=zip,
                enumerate=enumerate
            )

        except Exception as e:
            print(f"Ошибка: {e}")
            return render_template('index.html', error="Произошла ошибка при расчете. Попробуйте ещё раз.")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
