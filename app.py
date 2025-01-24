import io
import base64
import matplotlib.pyplot as plt

from flask import Flask, render_template, request

app = Flask(__name__)

# Прогнозные ставки по вкладам (на 5 лет, без капитализации)
DEPOSIT_RATES = [21.6, 18.5, 12.5, 8, 5]

# Словарь, где ключ — ставка налога (в %), значение — сумма годового вычета
TAX_DEDUCTIONS = {13: 19500, 15: 22500, 18: 27000, 20: 30000, 22: 33000}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Получение данных из формы
            annual_nsz_payment = float(request.form.get('annual_nsz_payment', 0))
            deposit_amount = float(request.form.get('deposit_amount', 0))
            tax_rate = int(request.form.get('tax_rate', 0))
            has_official_income = 'has_official_income' in request.form

            # Проверка ввода
            if annual_nsz_payment < 300000:
                return render_template('index.html', error="Сумма ежегодного взноса по НСЖ должна быть не менее 300 000 руб.")
            if tax_rate not in TAX_DEDUCTIONS:
                return render_template('index.html', error="Выберите корректную ставку налога из списка [13, 15, 18, 20, 22].")

            # Налоговая ставка в десятичном виде
            tax_rate_decimal = tax_rate / 100

            # Определение ставки кешбэка для НСЖ
            # (34% если 300 000 <= annual_nsz_payment < 500 000, 36% иначе)
            if 300000 <= annual_nsz_payment < 500000:
                nsz_cashback_rate = 0.34
            else:
                nsz_cashback_rate = 0.36

            # Общая сумма (для случая, когда всё хотим положить на вклад)
            total_initial_amount = deposit_amount + annual_nsz_payment

            # --- 1) Расчёт для случая "Только вклад" на ВСЮ сумму ---
            # NEW: берём всю сумму в качестве вклада.
            deposit_only_amount = deposit_amount + annual_nsz_payment

            deposit_only_income = []  # Доход по вкладу за каждый год (без капитализации)
            for rate in DEPOSIT_RATES:
                annual_income = deposit_only_amount * (rate / 100)  # проценты на вклад (вся сумма)
                net_income = annual_income * (1 - tax_rate_decimal) # вычитаем налог
                deposit_only_income.append(net_income)

            total_deposit_only_income = sum(deposit_only_income)

            # Итоговая сумма (вклад + все проценты)
            final_deposit_only_balance = deposit_only_amount + total_deposit_only_income

            # --- 2) Расчёт для случая "Вклад + НСЖ" ---
            # Здесь вклад = deposit_amount, а отдельно идёт ежегодный платёж в НСЖ
            deposit_split_income = []       # доход по вкладу (без капитализации)
            nsz_cashback_income = []        # кешбэк НСЖ
            nsz_tax_deduction_income = []   # налоговый вычет, если есть официальный доход

            for rate in DEPOSIT_RATES:
                # Доход по вкладу (только на deposit_amount)
                deposit_income = deposit_amount * (rate / 100)
                net_deposit_income = deposit_income * (1 - tax_rate_decimal)
                deposit_split_income.append(net_deposit_income)

                # Кешбэк по НСЖ
                nsz_cashback = annual_nsz_payment * nsz_cashback_rate
                nsz_net_cashback = nsz_cashback * (1 - tax_rate_decimal)
                nsz_cashback_income.append(nsz_net_cashback)

                # Налоговый вычет — умножаем на 2, если есть официальный доход
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

            # Итоговая сумма: deposit_amount + annual_nsz_payment + весь совокупный доход
            final_combined_split_balance = (
                deposit_amount
                + annual_nsz_payment
                + total_combined_split_income
            )

            # Разница
            difference = final_combined_split_balance - final_deposit_only_balance

            # --- 3) Построение графика ---
            years = list(range(1, len(DEPOSIT_RATES) + 1))
            plt.figure(figsize=(10, 6))

            # График для "Вклад (вся сумма)"
            deposit_balances_by_year = []
            for i in range(len(deposit_only_income)):
                balance_i = deposit_only_amount + sum(deposit_only_income[:i+1])
                deposit_balances_by_year.append(balance_i)

            plt.plot(years, deposit_balances_by_year, label="Вклад (вся сумма)")

            # График для комбинации "Вклад + НСЖ"
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

            # Сохранение графика в base64
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            graph_url = base64.b64encode(img.getvalue()).decode()
            plt.close()

            # Вывод отладочной инфы (по желанию)
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

            # Рендерим результат
            return render_template(
                'result.html',
                # Показатели "Только вклад (вся сумма)"
                deposit_only_income=deposit_only_income,
                total_deposit_only_income=total_deposit_only_income,
                final_deposit_only_balance=final_deposit_only_balance,

                # Показатели "Вклад + НСЖ"
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

    # Если GET-запрос — просто показываем страницу ввода
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
