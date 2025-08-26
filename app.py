import os
from flask import Flask, render_template, request, jsonify
import swisseph as swe
import matplotlib.pyplot as plt
from datetime import datetime

app = Flask(__name__, template_folder='templates')

os.makedirs('charts', exist_ok=True)

house_coords = {
    1: (1,3), 2: (0,3), 3: (0,2), 4: (0,1),
    5: (1,1), 6: (2,1), 7: (2,2), 8: (2,3),
    9: (1,2), 10: (1,0), 11: (0,0), 12: (2,0)
}

class VedicCalculator:
    def __init__(self):
        swe.set_ephe_path('')
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def get_jd(self, y, m, d, h, mi):
        return swe.julday(y, m, d, h + mi/60)

    def get_planets(self, jd):
        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE, 'Ketu': -1
        }
        pos = {}
        for planet, pid in planets.items():
            if planet == 'Ketu':
                lon = (pos['Rahu']['longitude'] + 180) % 360
            else:
                lon = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)[0][0]
            pos[planet] = {'longitude': lon,
                           'sign_num': int(lon / 30) + 1,
                           'degree': lon % 30}
        return pos

    def get_houses(self, jd, lat, lon):
        cusps, asc = swe.houses(jd, lat, lon, b'P')
        return cusps, asc

    def assign_houses(self, planets, asc):
        asc_sign = int(asc / 30) + 1
        planet_houses = {}
        for planet, data in planets.items():
            sign_num = data['sign_num']
            house_num = ((sign_num - asc_sign) % 12) + 1
            planet_houses[planet] = house_num
        return planet_houses

    def create_chart_data(self, y, m, d, h, mi, lat, lon):
        jd = self.get_jd(y, m, d, h, mi)
        planets = self.get_planets(jd)
        cusps, asc = self.get_houses(jd, lat, lon)
        planet_houses = self.assign_houses(planets, asc)
        return planets, planet_houses

def draw_chart(planets, planet_houses, filename):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.axis('off')

    for i in range(4):
        ax.plot([i, i], [0, 4], color='black')
        ax.plot([0, 4], [i, i], color='black')

    for house, (x, y) in house_coords.items():
        ax.text(x + 0.1, y + 0.1, str(house), fontsize=8, color='gray')

    for planet, data in planets.items():
        x, y = house_coords[planet_houses[planet]]
        ax.text(x + 0.4, y + 0.4, planet[0], fontsize=12, color='red')

    path = os.path.join('charts', filename)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    y, m, d = int(data['year']), int(data['month']), int(data['day'])
    h, mi = int(data['hour']), int(data['minute'])
    lat, lon = float(data['latitude']), float(data['longitude'])
    planets, planet_houses = VedicCalculator().create_chart_data(y, m, d, h, mi, lat, lon)
    filename = f"chart_{int(datetime.now().timestamp())}.png"
    chart_url = draw_chart(planets, planet_houses, filename)
    analysis = "Ascendant is in house " + str(planet_houses['Sun']) + ".\n(Analysis to be added.)"
    return jsonify(success=True, chart_url='/' + chart_url, predictions=analysis)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
