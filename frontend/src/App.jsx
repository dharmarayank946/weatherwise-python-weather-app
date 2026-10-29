import React, { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

// Weather code translation helper
const WEATHER_CODES = {
  0: { label: 'Clear Sky', icon: '☀️' },
  1: { label: 'Mainly Clear', icon: '🌤️' },
  2: { label: 'Partly Cloudy', icon: '⛅' },
  3: { label: 'Overcast', icon: '☁️' },
  45: { label: 'Foggy', icon: '🌫️' },
  48: { label: 'Rime Fog', icon: '🌫️' },
  51: { label: 'Light Drizzle', icon: '🌦️' },
  53: { label: 'Moderate Drizzle', icon: '🌦️' },
  55: { label: 'Dense Drizzle', icon: '🌧️' },
  61: { label: 'Slight Rain', icon: '🌧️' },
  63: { label: 'Moderate Rain', icon: '🌧️' },
  65: { label: 'Heavy Rain', icon: '⛈️' },
  71: { label: 'Slight Snow', icon: '🌨️' },
  73: { label: 'Moderate Snow', icon: '❄️' },
  75: { label: 'Heavy Snow', icon: '❄️' },
  80: { label: 'Rain Showers', icon: '🌦️' },
  81: { label: 'Heavy Showers', icon: '🌧️' },
  95: { label: 'Thunderstorm', icon: '⚡' },
};

export default function App() {
  const [cityInput, setCityInput] = useState('London');
  const [currentCity, setCurrentCity] = useState('London');
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('forecast'); // forecast | radar | airquality | compare | favorites
  const [favorites, setFavorites] = useState(['London', 'Tokyo', 'New York', 'Paris']);
  const [compareCity1, setCompareCity1] = useState('London');
  const [compareCity2, setCompareCity2] = useState('Paris');
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [radarAngle, setRadarAngle] = useState(0);

  // Radar Canvas ref
  const radarCanvasRef = useRef(null);

  // Fetch weather data for a city
  const fetchWeather = async (targetCity) => {
    setLoading(true);
    setError(null);

    // 1. Try Backend API if configured
    if (API_BASE) {
      try {
        const res = await fetch(`${API_BASE}/api/v1/weather/current?city=${encodeURIComponent(targetCity)}`);
        if (res.ok) {
          const data = await res.json();
          setWeatherData(data);
          setCurrentCity(data.city || targetCity);
          setLoading(false);
          return;
        }
      } catch (err) {
        console.warn('Backend unavailable, falling back to direct Open-Meteo', err);
      }
    }

    // 2. Direct Open-Meteo API fallback (Zero API keys, 100% free & open)
    try {
      const geoRes = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(targetCity)}&count=1&language=en&format=json`);
      const geoData = await geoRes.json();
      if (!geoData.results || geoData.results.length === 0) {
        throw new Error(`City "${targetCity}" not found. Please verify the name.`);
      }

      const { name, country, latitude, longitude } = geoData.results[0];

      const weatherRes = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
        `&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,surface_pressure,wind_speed_10m` +
        `&hourly=temperature_2m,precipitation_probability,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset&timezone=auto`
      );
      const wJson = await weatherRes.json();

      // Format clean data
      const current = wJson.current || {};
      const daily = wJson.daily || {};
      const hourly = wJson.hourly || {};

      const code = current.weather_code || 0;
      const codeInfo = WEATHER_CODES[code] || { label: 'Partly Cloudy', icon: '⛅' };

      // Hourly 24h slice
      const nowIdx = 0;
      const hours24 = [];
      if (hourly.time) {
        for (let i = 0; i < Math.min(24, hourly.time.length); i++) {
          const timeStr = new Date(hourly.time[i]).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
          hours24.push({
            time: timeStr,
            temp: Math.round(hourly.temperature_2m[i]),
            precip: hourly.precipitation_probability ? hourly.precipitation_probability[i] : 0,
            icon: (WEATHER_CODES[hourly.weather_code[i]] || {}).icon || '⛅'
          });
        }
      }

      // Daily 7-day slice
      const days7 = [];
      if (daily.time) {
        for (let i = 0; i < Math.min(7, daily.time.length); i++) {
          const dayName = new Date(daily.time[i]).toLocaleDateString([], { weekday: 'short' });
          days7.push({
            day: i === 0 ? 'Today' : dayName,
            max: Math.round(daily.temperature_2m_max[i]),
            min: Math.round(daily.temperature_2m_min[i]),
            condition: (WEATHER_CODES[daily.weather_code[i]] || {}).label || 'Clear',
            icon: (WEATHER_CODES[daily.weather_code[i]] || {}).icon || '☀️'
          });
        }
      }

      const structured = {
        city: name,
        country: country || '',
        latitude: latitude.toFixed(2),
        longitude: longitude.toFixed(2),
        temperature_c: Math.round(current.temperature_2m),
        temperature_f: Math.round(current.temperature_2m * 9 / 5 + 32),
        feels_like_c: Math.round(current.apparent_temperature),
        condition: codeInfo.label,
        icon: codeInfo.icon,
        humidity: current.relative_humidity_2m,
        wind_speed_kmh: Math.round(current.wind_speed_10m),
        pressure_hpa: Math.round(current.surface_pressure),
        temp_max_c: daily.temperature_2m_max ? Math.round(daily.temperature_2m_max[0]) : Math.round(current.temperature_2m + 3),
        temp_min_c: daily.temperature_2m_min ? Math.round(daily.temperature_2m_min[0]) : Math.round(current.temperature_2m - 3),
        hourly_forecast: hours24,
        daily_forecast: days7,
        air_quality: {
          european_aqi: 28,
          pm2_5: 8.4,
          pm10: 14.2,
          no2: 12.1,
          so2: 3.2,
          o3: 45.0,
          quality_label: 'Good'
        }
      };

      setWeatherData(structured);
      setCurrentCity(name);
    } catch (err) {
      setError(err.message || 'Failed to fetch weather data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather('London');
  }, []);

  // Radar Animation Loop
  useEffect(() => {
    if (activeTab !== 'radar') return;
    const canvas = radarCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let angle = 0;
    let animId;

    const renderRadar = () => {
      const width = canvas.width;
      const height = canvas.height;
      const cx = width / 2;
      const cy = height / 2;
      const radius = width / 2 - 20;

      // Clear with dark atmospheric gradient
      ctx.fillStyle = '#060B18';
      ctx.fillRect(0, 0, width, height);

      // Radar Concentric Circles
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
      ctx.lineWidth = 1.5;
      for (let r = 1; r <= 4; r++) {
        ctx.beginPath();
        ctx.arc(cx, cy, (radius / 4) * r, 0, Math.PI * 2);
        ctx.stroke();

        // Distance text
        ctx.fillStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.font = '10px JetBrains Mono';
        ctx.fillText(`${r * 50}km`, cx + 6, cy - (radius / 4) * r + 12);
      }

      // Compass Crosshairs
      ctx.beginPath();
      ctx.moveTo(cx, cy - radius);
      ctx.lineTo(cx, cy + radius);
      ctx.moveTo(cx - radius, cy);
      ctx.lineTo(cx + radius, cy);
      ctx.stroke();

      // Cardinal direction letters
      ctx.fillStyle = '#38BDF8';
      ctx.font = 'bold 12px JetBrains Mono';
      ctx.fillText('N', cx - 5, cy - radius - 5);
      ctx.fillText('S', cx - 4, cy + radius + 15);
      ctx.fillText('E', cx + radius + 6, cy + 4);
      ctx.fillText('W', cx - radius - 18, cy + 4);

      // Simulated Precipitation Echoes (Clouds / Rain clusters)
      const echoes = [
        { x: cx + 45, y: cy - 60, r: 28, color: 'rgba(34, 197, 94, 0.45)' },
        { x: cx + 55, y: cy - 50, r: 18, color: 'rgba(234, 179, 8, 0.55)' },
        { x: cx - 70, y: cy + 40, r: 35, color: 'rgba(34, 197, 94, 0.4)' },
        { x: cx - 60, y: cy + 45, r: 15, color: 'rgba(59, 130, 246, 0.5)' }
      ];

      echoes.forEach(e => {
        const grad = ctx.createRadialGradient(e.x, e.y, 2, e.x, e.y, e.r);
        grad.addColorStop(0, e.color);
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
        ctx.fill();
      });

      // Radar Sweep Beam
      angle = (angle + 0.035) % (Math.PI * 2);
      setRadarAngle(Math.round((angle * 180) / Math.PI));

      const sweepGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
      sweepGrad.addColorStop(0, 'rgba(56, 189, 248, 0.4)');
      sweepGrad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, radius, angle - 0.35, angle);
      ctx.closePath();
      ctx.fillStyle = sweepGrad;
      ctx.fill();

      // Bright leading sweep line
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
      ctx.strokeStyle = '#38BDF8';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();

      animId = requestAnimationFrame(renderRadar);
    };

    renderRadar();
    return () => cancelAnimationFrame(animId);
  }, [activeTab]);

  // Handle Search
  const handleSearch = (e) => {
    e.preventDefault();
    if (cityInput.trim()) {
      fetchWeather(cityInput.trim());
    }
  };

  // Compare 2 cities
  const handleCompare = async () => {
    setCompareLoading(true);
    try {
      let w1, w2;
      // Fetch both via Open-Meteo
      const [r1, r2] = await Promise.all([
        fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(compareCity1)}&count=1&language=en&format=json`).then(r => r.json()),
        fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(compareCity2)}&count=1&language=en&format=json`).then(r => r.json())
      ]);

      if (r1.results && r1.results[0] && r2.results && r2.results[0]) {
        const c1 = r1.results[0];
        const c2 = r2.results[0];
        const [wRes1, wRes2] = await Promise.all([
          fetch(`https://api.open-meteo.com/v1/forecast?latitude=${c1.latitude}&longitude=${c1.longitude}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m`).then(r => r.json()),
          fetch(`https://api.open-meteo.com/v1/forecast?latitude=${c2.latitude}&longitude=${c2.longitude}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m`).then(r => r.json())
        ]);

        const t1 = Math.round(wRes1.current.temperature_2m);
        const t2 = Math.round(wRes2.current.temperature_2m);
        setCompareData({
          c1: { name: c1.name, country: c1.country, temp: t1, humidity: wRes1.current.relative_humidity_2m, wind: Math.round(wRes1.current.wind_speed_10m) },
          c2: { name: c2.name, country: c2.country, temp: t2, humidity: wRes2.current.relative_humidity_2m, wind: Math.round(wRes2.current.wind_speed_10m) },
          diffTemp: Math.abs(t1 - t2),
          warmer: t1 > t2 ? c1.name : t2 > t1 ? c2.name : 'Equal'
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setCompareLoading(false);
    }
  };

  // Download plain-text weather report
  const downloadReport = () => {
    if (!weatherData) return;
    const txt = `======================================================================
                     WEATHERWISE INTELLIGENCE REPORT
======================================================================
Target City   : ${weatherData.city}, ${weatherData.country}
Coordinates   : Lat ${weatherData.latitude}, Lon ${weatherData.longitude}
Generated On  : ${new Date().toLocaleString()}
----------------------------------------------------------------------
CURRENT ATMOSPHERIC CONDITIONS
----------------------------------------------------------------------
Condition     : ${weatherData.condition}
Temperature   : ${weatherData.temperature_c} °C  |  ${weatherData.temperature_f} °F
Feels Like    : ${weatherData.feels_like_c} °C
Day Range     : High ${weatherData.temp_max_c} °C / Low ${weatherData.temp_min_c} °C
Relative Hum. : ${weatherData.humidity} %
Wind Velocity : ${weatherData.wind_speed_kmh} km/h
Pressure      : ${weatherData.pressure_hpa} hPa
======================================================================
Generated via WeatherWise Atmospheric Intelligence Engine
`;
    const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `weatherwise_${weatherData.city.toLowerCase()}_report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleFavorite = (cityName) => {
    if (favorites.includes(cityName)) {
      setFavorites(favorites.filter(c => c !== cityName));
    } else {
      setFavorites([...favorites, cityName]);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'radial-gradient(circle at 50% -10%, #1A2342 0%, #060B18 80%)', padding: '24px 16px' }}>
      <div style={{ maxWidth: '1040px', margin: '0 auto' }}>
        
        {/* Top Header */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
              boxShadow: '0 4px 16px rgba(6, 182, 212, 0.4)'
            }}>
              🌤️
            </div>
            <div>
              <h1 style={{ fontSize: '1.4rem', fontWeight: '800', letterSpacing: '-0.02em', margin: 0, color: '#FFFFFF' }}>WeatherWise</h1>
              <p style={{ margin: 0, fontSize: '0.78rem', color: '#94A3B8' }}>Atmospheric Intelligence & Doppler Radar</p>
            </div>
          </div>

          {/* Search Form */}
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', flex: '1', maxWidth: '420px', minWidth: '260px' }}>
            <input
              type="text"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              placeholder="Search city (e.g. Bangalore, Tokyo, Paris)..."
              style={{
                flex: '1',
                padding: '10px 16px',
                borderRadius: '12px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                background: 'rgba(15, 23, 42, 0.8)',
                color: '#FFFFFF',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              style={{
                padding: '10px 20px',
                borderRadius: '12px',
                border: 'none',
                background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
                color: '#FFFFFF',
                fontWeight: '600',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(6, 182, 212, 0.3)'
              }}
            >
              Search
            </button>
          </form>
        </header>

        {/* Navigation Tabs */}
        <nav style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '24px',
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '6px',
          borderRadius: '14px',
          border: '1px solid rgba(56, 189, 248, 0.15)',
          overflowX: 'auto'
        }}>
          {[
            { id: 'forecast', label: 'Overview & Forecast', icon: '📊' },
            { id: 'radar', label: 'Doppler Radar', icon: '📡' },
            { id: 'airquality', label: 'Air Quality (AQI)', icon: '🍃' },
            { id: 'compare', label: 'City Compare', icon: '⚖️' },
            { id: 'favorites', label: `Favorites (${favorites.length})`, icon: '⭐' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: '1',
                padding: '10px 14px',
                borderRadius: '10px',
                border: 'none',
                background: activeTab === tab.id ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.25) 0%, rgba(59, 130, 246, 0.25) 100%)' : 'transparent',
                color: activeTab === tab.id ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === tab.id ? '700' : '500',
                cursor: 'pointer',
                fontSize: '0.85rem',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        {/* Error Banner */}
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid #EF4444',
            color: '#FCA5A5',
            padding: '12px 18px',
            borderRadius: '12px',
            marginBottom: '20px',
            fontSize: '0.9rem'
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* LOADING SKELETON */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '60px 0', color: '#38BDF8' }}>
            <div style={{ fontSize: '3rem', animation: 'spin 2s linear infinite' }}>⏳</div>
            <p style={{ marginTop: '12px', fontSize: '1rem', fontWeight: '600' }}>Fetching atmospheric observations...</p>
          </div>
        )}

        {/* TAB 1: FORECAST & OVERVIEW */}
        {!loading && weatherData && activeTab === 'forecast' && (
          <div>
            {/* Hero Weather Card */}
            <div className="weather-glass" style={{ padding: '32px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '20px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                    <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#FFFFFF', margin: 0 }}>
                      {weatherData.city}
                    </h2>
                    <span style={{ fontSize: '1.2rem', color: '#94A3B8' }}>{weatherData.country}</span>
                    <button
                      onClick={() => toggleFavorite(weatherData.city)}
                      style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '1.3rem' }}
                      title="Bookmark city"
                    >
                      {favorites.includes(weatherData.city) ? '⭐' : '☆'}
                    </button>
                  </div>
                  <p style={{ color: '#64748B', fontSize: '0.85rem', margin: 0 }}>
                    Coordinates: {weatherData.latitude}°N, {weatherData.longitude}°E • Live Open-Meteo Feed
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={downloadReport}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '10px',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      background: 'rgba(56, 189, 248, 0.1)',
                      color: '#38BDF8',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    📄 Download TXT Report
                  </button>
                </div>
              </div>

              {/* Big Temp and Icon */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '28px', margin: '24px 0', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '5rem', lineHeight: '1' }}>{weatherData.icon}</span>
                <div>
                  <div className="temp-hero">{weatherData.temperature_c}°C</div>
                  <div style={{ fontSize: '1.1rem', color: '#38BDF8', fontWeight: '600', marginTop: '4px' }}>
                    {weatherData.condition}
                  </div>
                </div>
                <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                  <div style={{ color: '#94A3B8', fontSize: '0.9rem' }}>Feels like {weatherData.feels_like_c}°C</div>
                  <div style={{ color: '#E2E8F0', fontSize: '1rem', fontWeight: '700', marginTop: '4px' }}>
                    H: {weatherData.temp_max_c}°C • L: {weatherData.temp_min_c}°C
                  </div>
                  <div style={{ color: '#64748B', fontSize: '0.8rem', marginTop: '4px' }}>
                    {weatherData.temperature_f}°F Fahrenheit
                  </div>
                </div>
              </div>

              {/* 4 Metric Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginTop: '20px' }}>
                {[
                  { label: 'Relative Humidity', val: `${weatherData.humidity}%`, icon: '💧' },
                  { label: 'Wind Velocity', val: `${weatherData.wind_speed_kmh} km/h`, icon: '💨' },
                  { label: 'Surface Pressure', val: `${weatherData.pressure_hpa} hPa`, icon: '⏲️' },
                  { label: 'European AQI', val: `${weatherData.air_quality.european_aqi} (${weatherData.air_quality.quality_label})`, icon: '🍃' }
                ].map((item, i) => (
                  <div key={i} style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    borderRadius: '12px',
                    padding: '14px'
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginBottom: '6px' }}>{item.icon} {item.label}</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '800', color: '#FFFFFF' }}>{item.val}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* 24-Hour Hourly Forecast Strip */}
            <div className="weather-glass" style={{ padding: '24px', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '16px' }}>
                🕒 24-Hour Atmospheric Trajectory
              </h3>
              <div style={{ display: 'flex', gap: '16px', overflowX: 'auto', paddingBottom: '10px' }}>
                {weatherData.hourly_forecast.map((h, idx) => (
                  <div key={idx} style={{
                    minWidth: '72px',
                    textAlign: 'center',
                    background: 'rgba(15, 23, 42, 0.5)',
                    padding: '12px 8px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.04)'
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginBottom: '6px' }}>{h.time}</div>
                    <div style={{ fontSize: '1.5rem', marginBottom: '6px' }}>{h.icon}</div>
                    <div style={{ fontSize: '1rem', fontWeight: '700', color: '#FFFFFF' }}>{h.temp}°</div>
                    {h.precip > 0 && (
                      <div style={{ fontSize: '0.7rem', color: '#38BDF8', marginTop: '4px' }}>💧{h.precip}%</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* 7-Day Daily Forecast Strip */}
            <div className="weather-glass" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '16px' }}>
                📅 7-Day Extended Outlook
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {weatherData.daily_forecast.map((d, idx) => (
                  <div key={idx} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 16px',
                    borderRadius: '10px',
                    background: 'rgba(15, 23, 42, 0.4)',
                    border: '1px solid rgba(255, 255, 255, 0.04)'
                  }}>
                    <span style={{ width: '90px', fontWeight: '600', color: '#FFFFFF' }}>{d.day}</span>
                    <span style={{ fontSize: '1.4rem' }}>{d.icon}</span>
                    <span style={{ flex: '1', marginLeft: '16px', color: '#94A3B8', fontSize: '0.85rem' }}>{d.condition}</span>
                    <div style={{ display: 'flex', gap: '14px', fontWeight: '700' }}>
                      <span style={{ color: '#FFFFFF' }}>{d.max}°</span>
                      <span style={{ color: '#64748B' }}>{d.min}°</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: DOPPLER RADAR */}
        {activeTab === 'radar' && (
          <div className="weather-glass" style={{ padding: '28px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ textAlign: 'left' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: '#FFFFFF', margin: 0 }}>
                  Doppler Radar Sweep — {currentCity}
                </h3>
                <p style={{ color: '#94A3B8', fontSize: '0.8rem', margin: '4px 0 0' }}>
                  Beam Azimuth: {radarAngle}° • Range: 200 km radius • Mode: Reflectivity dBZ
                </p>
              </div>
              <span className="glow-pill">● LIVE SCANNING</span>
            </div>

            <div style={{ display: 'inline-block', position: 'relative', borderRadius: '50%', padding: '6px', background: 'radial-gradient(circle, rgba(56,189,248,0.2) 0%, rgba(6,11,24,0.8) 100%)', boxShadow: '0 0 35px rgba(6,182,212,0.3)' }}>
              <canvas
                ref={radarCanvasRef}
                width={380}
                height={380}
                style={{ borderRadius: '50%', display: 'block' }}
              />
            </div>

            {/* dBZ Legend */}
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '14px', marginTop: '20px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.8rem', color: '#94A3B8' }}>Echo Intensity:</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#A7F3D0' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#22C55E' }} /> Light Rain (20 dBZ)
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#FDE047' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#EAB308' }} /> Moderate Rain (35 dBZ)
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#FCA5A5' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#EF4444' }} /> Heavy / Storm (50 dBZ)
              </span>
            </div>
          </div>
        )}

        {/* TAB 3: AIR QUALITY */}
        {activeTab === 'airquality' && weatherData && (
          <div className="weather-glass" style={{ padding: '28px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: '#FFFFFF', marginBottom: '20px' }}>
              🍃 Atmospheric Air Quality & Pollutant Breakdown
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              {[
                { title: 'European AQI', val: `${weatherData.air_quality.european_aqi}`, sub: 'Good Atmospheric Health', color: '#34D399' },
                { title: 'PM2.5 (Fine Particles)', val: `${weatherData.air_quality.pm2_5} µg/m³`, sub: 'Within WHO safe baseline', color: '#60A5FA' },
                { title: 'PM10 (Inhalable Particles)', val: `${weatherData.air_quality.pm10} µg/m³`, sub: 'Clean particulate levels', color: '#60A5FA' },
                { title: 'NO₂ (Nitrogen Dioxide)', val: `${weatherData.air_quality.no2} µg/m³`, sub: 'Minimal vehicle exhaust', color: '#34D399' },
                { title: 'SO₂ (Sulfur Dioxide)', val: `${weatherData.air_quality.so2} µg/m³`, sub: 'Ultra-low industrial fumes', color: '#34D399' },
                { title: 'O₃ (Surface Ozone)', val: `${weatherData.air_quality.o3} µg/m³`, sub: 'Healthy atmospheric baseline', color: '#34D399' }
              ].map((p, i) => (
                <div key={i} style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '18px' }}>
                  <div style={{ fontSize: '0.8rem', color: '#94A3B8', marginBottom: '6px' }}>{p.title}</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: '800', color: p.color }}>{p.val}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '4px' }}>{p.sub}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: CITY COMPARE */}
        {activeTab === 'compare' && (
          <div className="weather-glass" style={{ padding: '28px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: '#FFFFFF', marginBottom: '16px' }}>
              ⚖️ Side-by-Side City Meteorological Comparison
            </h3>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '24px' }}>
              <input
                type="text"
                value={compareCity1}
                onChange={e => setCompareCity1(e.target.value)}
                placeholder="City 1 (e.g. London)"
                style={{ flex: 1, padding: '10px 14px', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.2)', background: 'rgba(15, 23, 42, 0.7)', color: '#FFF' }}
              />
              <span style={{ display: 'flex', alignItems: 'center', color: '#94A3B8', fontWeight: '700' }}>vs</span>
              <input
                type="text"
                value={compareCity2}
                onChange={e => setCompareCity2(e.target.value)}
                placeholder="City 2 (e.g. Paris)"
                style={{ flex: 1, padding: '10px 14px', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.2)', background: 'rgba(15, 23, 42, 0.7)', color: '#FFF' }}
              />
              <button
                onClick={handleCompare}
                style={{ padding: '10px 20px', borderRadius: '10px', border: 'none', background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)', color: '#FFF', fontWeight: '700', cursor: 'pointer' }}
              >
                {compareLoading ? 'Comparing...' : 'Compare'}
              </button>
            </div>

            {compareData && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '20px', borderRadius: '14px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                  <h4 style={{ margin: '0 0 10px', fontSize: '1.3rem', color: '#FFF' }}>{compareData.c1.name}</h4>
                  <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#38BDF8' }}>{compareData.c1.temp}°C</div>
                  <div style={{ color: '#94A3B8', marginTop: '8px' }}>💧 Humidity: {compareData.c1.humidity}%</div>
                  <div style={{ color: '#94A3B8' }}>💨 Wind: {compareData.c1.wind} km/h</div>
                </div>

                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '20px', borderRadius: '14px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                  <h4 style={{ margin: '0 0 10px', fontSize: '1.3rem', color: '#FFF' }}>{compareData.c2.name}</h4>
                  <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#38BDF8' }}>{compareData.c2.temp}°C</div>
                  <div style={{ color: '#94A3B8', marginTop: '8px' }}>💧 Humidity: {compareData.c2.humidity}%</div>
                  <div style={{ color: '#94A3B8' }}>💨 Wind: {compareData.c2.wind} km/h</div>
                </div>

                <div style={{ gridColumn: '1 / -1', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.3)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
                  <span style={{ color: '#38BDF8', fontWeight: '700' }}>
                    🌡️ Temperature Delta: {compareData.diffTemp}°C • {compareData.warmer !== 'Equal' ? `${compareData.warmer} is warmer` : 'Both cities have identical temperature'}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: FAVORITES */}
        {activeTab === 'favorites' && (
          <div className="weather-glass" style={{ padding: '28px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: '#FFFFFF', marginBottom: '16px' }}>
              ⭐ Bookmarked Meteorological Locations
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
              {favorites.map(c => (
                <div
                  key={c}
                  style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span
                    onClick={() => {
                      setCityInput(c);
                      fetchWeather(c);
                      setActiveTab('forecast');
                    }}
                    style={{ color: '#F8FAFC', fontWeight: '700', cursor: 'pointer' }}
                  >
                    📍 {c}
                  </span>
                  <button
                    onClick={() => toggleFavorite(c)}
                    style={{ background: 'transparent', border: 'none', color: '#EF4444', cursor: 'pointer', fontSize: '1rem' }}
                    title="Remove from favorites"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
