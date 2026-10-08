{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Demo: Tính toán Sản lượng Điện Mặt Trời tại Gia Lai\n",
    "\n",
    "Notebook này minh họa Module 1 — `solar-physics-vn`:\n",
    "- Phân vùng khí hậu Việt Nam\n",
    "- Ước tính sản lượng cho hệ thống 10 kWp tại Gia Lai\n",
    "- So sánh sản lượng các vùng khí hậu chính"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import sys, os\n",
    "sys.path.insert(0, os.path.join('..', 'solar-physics-vn'))\n",
    "sys.path.insert(0, os.path.join('..', 'nlp-chatbot-interface'))\n",
    "\n",
    "from climate_zones import VIETNAM_CLIMATE_ZONES, get_climate_zone\n",
    "import pandas as pd\n",
    "\n",
    "print('Các vùng khí hậu Việt Nam:')\n",
    "for code, zone in VIETNAM_CLIMATE_ZONES.items():\n",
    "    print(f'  [{code}] {zone.name}')\n",
    "    print(f'    GHI: {zone.ghi_annual_avg} kWh/m²/ngày | Nhiệt độ TB: {zone.temp_avg_c}°C | Góc nghiêng tối ưu: {zone.optimal_tilt}°')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# So sánh sản lượng ước tính 10 kWp theo từng vùng\n",
    "capacity_kwp = 10.0\n",
    "pr = 0.78  # Performance Ratio trung bình\n",
    "\n",
    "results = []\n",
    "for code, zone in VIETNAM_CLIMATE_ZONES.items():\n",
    "    annual_yield = capacity_kwp * zone.ghi_annual_avg * 365 * pr\n",
    "    results.append({\n",
    "        'Vùng khí hậu': zone.name.split(' — ')[0],\n",
    "        'GHI (kWh/m²/ngày)': zone.ghi_annual_avg,\n",
    "        'Sản lượng năm (kWh)': round(annual_yield),\n",
    "        'Specific Yield (kWh/kWp)': round(annual_yield / capacity_kwp),\n",
    "    })\n",
    "\n",
    "df = pd.DataFrame(results)\n",
    "print(df.to_string(index=False))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Demo Text-to-Solar NER\n",
    "from ner_extractor import SolarNERExtractor\n",
    "\n",
    "ner = SolarNERExtractor()\n",
    "test_queries = [\n",
    "    'Nhà tôi ở Gia Lai, mái hướng Nam, diện tích 50m², tiền điện 2 triệu/tháng',\n",
    "    'Xưởng ở Bình Dương, mái tôn 500m², muốn đầu tư hệ thống tự sản tự tiêu',\n",
    "    'Hộ gia đình tại Đà Nẵng, hướng Đông Nam, hóa đơn điện 800 nghìn/tháng',\n",
    "]\n",
    "\n",
    "for q in test_queries:\n",
    "    result = ner.extract(q)\n",
    "    print(f'\\nInput: {q}')\n",
    "    print(f'  → Địa điểm : {result.location}')\n",
    "    print(f'  → Hướng    : {result.roof_direction}')\n",
    "    print(f'  → Diện tích: {result.roof_area_m2} m²')\n",
    "    print(f'  → Tiền điện: {result.monthly_bill_vnd:,.0f} đ/tháng' if result.monthly_bill_vnd else '  → Tiền điện: N/A')\n",
    "    print(f'  → Mục tiêu : {result.goal}')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Demo Text-to-Solar Engine — Báo cáo đầy đủ\n",
    "from text_to_solar import TextToSolarEngine\n",
    "\n",
    "engine = TextToSolarEngine(use_pvlib=False)  # offline mode\n",
    "query = 'Nhà tôi ở Gia Lai, mái tôn hướng Nam, diện tích 50m², tiền điện 2 triệu/tháng, muốn tiết kiệm'\n",
    "\n",
    "report = engine.analyze(query)\n",
    "print(report.to_vietnamese())"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Vẽ biểu đồ so sánh GHI các vùng\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib\n",
    "matplotlib.rcParams['font.family'] = 'DejaVu Sans'\n",
    "\n",
    "zones = list(VIETNAM_CLIMATE_ZONES.values())\n",
    "names = [z.name.split(' — ')[0] for z in zones]\n",
    "ghis = [z.ghi_annual_avg for z in zones]\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(9, 4))\n",
    "bars = ax.barh(names, ghis, color=['#3b82d4' if g >= 5.0 else '#7c5cd8' for g in ghis])\n",
    "ax.axvline(x=5.0, color='orange', linestyle='--', linewidth=1.2, label='Ngưỡng tiềm năng cao (5.0)')\n",
    "ax.set_xlabel('Bức xạ nằm ngang toàn phần trung bình (kWh/m²/ngày)')\n",
    "ax.set_title('Tiềm năng Điện Mặt Trời theo Vùng Khí hậu Việt Nam')\n",
    "ax.legend()\n",
    "for bar, val in zip(bars, ghis):\n",
    "    ax.text(val + 0.05, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=9)\n",
    "plt.tight_layout()\n",
    "plt.savefig('../docs/vietnam_solar_potential.png', dpi=150, bbox_inches='tight')\n",
    "plt.show()\n",
    "print('Biểu đồ đã lưu vào docs/vietnam_solar_potential.png')"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.10.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
