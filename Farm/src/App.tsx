import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Brush,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import mqtt, { type MqttClient } from 'mqtt'
import { fetchSensorHistory } from './api/sensorApi'
import type { SensorReading } from './types/sensor'
import './App.css'

type MetricKey = 'temperature' | 'humidity' | 'soilRaw' | 'soilPercent'

interface MetricConfig {
  title: string
  valueKey: MetricKey
  unit: string
  stroke: string
}

type ControlKey = 'temperature' | 'soil'
type MqttStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

const METRICS: MetricConfig[] = [
  { title: 'Temperature', valueKey: 'temperature', unit: '°C', stroke: '#ef4444' },
  { title: 'Humidity', valueKey: 'humidity', unit: '%', stroke: '#3b82f6' },
  { title: 'Soil Raw', valueKey: 'soilRaw', unit: '', stroke: '#8b5cf6' },
  { title: 'Soil Percent', valueKey: 'soilPercent', unit: '%', stroke: '#10b981' },
]

function ControlCard({
  title,
  enabled,
  pending,
  onToggle,
}: {
  title: string
  enabled: boolean
  pending: boolean
  onToggle: () => void
}) {
  return (
    <article className="control-card">
      <div>
        <h3>{title}</h3>
        <p>{enabled ? 'ON' : 'OFF'}</p>
      </div>
      <button
        type="button"
        className={`toggle-switch ${enabled ? 'on' : 'off'}`}
        onClick={onToggle}
        disabled={pending}
        aria-pressed={enabled}
      >
        <span className="toggle-thumb" />
      </button>
    </article>
  )
}

function MetricChart({
  data,
  metric,
}: {
  data: SensorReading[]
  metric: MetricConfig
}) {
  const totalPoints = data.length
  const defaultWindow = Math.min(20, totalPoints)
  const defaultStart = Math.max(0, totalPoints - defaultWindow)
  const defaultEnd = Math.max(0, totalPoints - 1)

  const [range, setRange] = useState<{ start: number; end: number } | null>(null)

  const currentStart =
    range == null ? defaultStart : Math.min(Math.max(0, range.start), defaultEnd)
  const currentEnd =
    range == null
      ? defaultEnd
      : Math.min(Math.max(currentStart, range.end), defaultEnd)

  const visibleData = data.slice(currentStart, currentEnd + 1)

  const latestMetricValue = useMemo(() => {
    for (let index = data.length - 1; index >= 0; index -= 1) {
      const value = data[index][metric.valueKey]
      if (value != null) {
        return value
      }
    }

    return null
  }, [data, metric.valueKey])

  const { minValue, maxValue } = useMemo(() => {
    if (visibleData.length === 0) {
      return { minValue: 0, maxValue: 1 }
    }

    let min = Number.POSITIVE_INFINITY
    let max = Number.NEGATIVE_INFINITY

    for (const item of visibleData) {
      const value = item[metric.valueKey]
      if (value == null) {
        continue
      }

      if (value < min) {
        min = value
      }
      if (value > max) {
        max = value
      }
    }

    if (min === Number.POSITIVE_INFINITY || max === Number.NEGATIVE_INFINITY) {
      return { minValue: 0, maxValue: 1 }
    }

    return { minValue: min, maxValue: max }
  }, [metric.valueKey, visibleData])

  const rangeSpan = maxValue - minValue
  const yPadding = rangeSpan === 0 ? Math.max(1, Math.abs(maxValue) * 0.02) : rangeSpan * 0.2
  const yDomain: [number, number] = [minValue - yPadding, maxValue + yPadding]

  const zoomIn = () => {
    const span = currentEnd - currentStart + 1
    if (span <= 6) {
      return
    }

    const nextSpan = Math.max(6, Math.floor(span * 0.7))
    const center = Math.floor((currentStart + currentEnd) / 2)
    let nextStart = center - Math.floor(nextSpan / 2)
    let nextEnd = nextStart + nextSpan - 1

    if (nextStart < 0) {
      nextStart = 0
      nextEnd = nextSpan - 1
    }

    if (nextEnd > defaultEnd) {
      nextEnd = defaultEnd
      nextStart = Math.max(0, nextEnd - nextSpan + 1)
    }

    setRange({ start: nextStart, end: nextEnd })
  }

  const zoomOut = () => {
    const span = currentEnd - currentStart + 1
    if (span >= totalPoints) {
      return
    }

    const nextSpan = Math.min(totalPoints, Math.ceil(span * 1.35))
    const center = Math.floor((currentStart + currentEnd) / 2)
    let nextStart = center - Math.floor(nextSpan / 2)
    let nextEnd = nextStart + nextSpan - 1

    if (nextStart < 0) {
      nextStart = 0
      nextEnd = nextSpan - 1
    }

    if (nextEnd > defaultEnd) {
      nextEnd = defaultEnd
      nextStart = Math.max(0, nextEnd - nextSpan + 1)
    }

    setRange({ start: nextStart, end: nextEnd })
  }

  const resetZoom = () => {
    setRange(null)
  }

  return (
    <article className="chart-card">
      <div className="chart-head">
        <h2>{metric.title}</h2>
        <p className="value-pill">
          {latestMetricValue != null ? `${latestMetricValue.toFixed(1)}${metric.unit}` : '--'}
        </p>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 0, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="createdAt"
              reversed
              tickFormatter={(value: string) => new Date(value).toLocaleTimeString()}
              minTickGap={24}
            />
            <YAxis width={48} domain={yDomain} />
            <Tooltip
              formatter={(value: number | string) => {
                const numeric = typeof value === 'number' ? value : Number(value)
                if (Number.isNaN(numeric)) {
                  return '--'
                }

                return `${numeric.toFixed(2)}${metric.unit}`
              }}
              labelFormatter={(value: string) => new Date(value).toLocaleString()}
            />
            <Line
              type="monotone"
              dataKey={metric.valueKey}
              stroke={metric.stroke}
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5 }}
            />
            <Brush
              dataKey="createdAt"
              startIndex={currentStart}
              endIndex={currentEnd}
              travellerWidth={12}
              height={28}
              onChange={(next) => {
                if (
                  next &&
                  typeof next.startIndex === 'number' &&
                  typeof next.endIndex === 'number'
                ) {
                  setRange({ start: next.startIndex, end: next.endIndex })
                }
              }}
              tickFormatter={(value: string) => new Date(value).toLocaleTimeString()}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="zoom-controls">
        <button type="button" className="zoom-button" onClick={zoomOut}>
          Zoom -
        </button>
        <button type="button" className="zoom-button" onClick={zoomIn}>
          Zoom +
        </button>
        <button type="button" className="zoom-button" onClick={resetZoom}>
          Reset
        </button>
      </div>
    </article>
  )
}

function App() {
  const adafruitUsername = import.meta.env.VITE_ADAFRUIT_USERNAME as string | undefined
  const adafruitKey = import.meta.env.VITE_ADAFRUIT_KEY as string | undefined
  const mqttUrl =
    (import.meta.env.VITE_ADAFRUIT_MQTT_URL as string | undefined) ??
    'wss://io.adafruit.com:443/mqtt/'

  const temperatureFeed =
    (import.meta.env.VITE_ADAFRUIT_TEMP_FEED as string | undefined) ??
    `${adafruitUsername}/feeds/control-dht-enable`
  const soilFeed =
    (import.meta.env.VITE_ADAFRUIT_SOIL_FEED as string | undefined) ??
    `${adafruitUsername}/feeds/control-soil-enable`

  const hasMqttConfig = Boolean(adafruitUsername && adafruitKey)

  const [readings, setReadings] = useState<SensorReading[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mqttStatus, setMqttStatus] = useState<MqttStatus>(
    hasMqttConfig ? 'connecting' : 'error',
  )
  const [mqttError, setMqttError] = useState<string | null>(null)
  const [controls, setControls] = useState<Record<ControlKey, boolean>>({
    temperature: false,
    soil: false,
  })
  const [controlPending, setControlPending] = useState<Record<ControlKey, boolean>>({
    temperature: false,
    soil: false,
  })
  const mqttClientRef = useRef<MqttClient | null>(null)

  const feedByKey = useMemo<Record<ControlKey, string>>(
    () => ({
      temperature: temperatureFeed,
      soil: soilFeed,
    }),
    [soilFeed, temperatureFeed],
  )

  const getFeedKeyFromTopic = useCallback((topic: string) => {
    const segments = topic.split('/')
    return segments[segments.length - 1]
  }, [])

  const syncControlStates = useCallback(async () => {
    if (!adafruitUsername || !adafruitKey) {
      return
    }

    try {
      const tempFeedKey = getFeedKeyFromTopic(temperatureFeed)
      const soilFeedKey = getFeedKeyFromTopic(soilFeed)

      const [tempRes, soilRes] = await Promise.all([
        fetch(`https://io.adafruit.com/api/v2/${adafruitUsername}/feeds/${tempFeedKey}/data/last`, {
          headers: { 'X-AIO-Key': adafruitKey },
        }),
        fetch(`https://io.adafruit.com/api/v2/${adafruitUsername}/feeds/${soilFeedKey}/data/last`, {
          headers: { 'X-AIO-Key': adafruitKey },
        }),
      ])

      if (!tempRes.ok || !soilRes.ok) {
        throw new Error('Failed to fetch latest switch values from Adafruit')
      }

      const [tempData, soilData] = await Promise.all([tempRes.json(), soilRes.json()])

      setControls({
        temperature: String(tempData?.value).trim() === '1',
        soil: String(soilData?.value).trim() === '1',
      })
      setControlPending({ temperature: false, soil: false })
      setMqttError(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to sync switches'
      setMqttError(message)
    }
  }, [adafruitKey, adafruitUsername, getFeedKeyFromTopic, soilFeed, temperatureFeed])

  const keyByFeed = useMemo<Record<string, ControlKey>>(
    () => ({
      [temperatureFeed]: 'temperature',
      [soilFeed]: 'soil',
    }),
    [soilFeed, temperatureFeed],
  )

  const loadSensorData = useCallback(async (silent = false) => {
    if (!silent) {
      setLoading(true)
    }

    setError(null)

    try {
      const history = await fetchSensorHistory(60)
      setReadings(history)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(message)
    } finally {
      if (!silent) {
        setLoading(false)
      }
    }
  }, [])

    // auto-refresh every 12s (silent chart load + switch sync)
    useEffect(() => {
        const interval = setInterval(() => {
            void loadSensorData(true) // silent = true to avoid flicker
            void syncControlStates()
        }, 12_000)

        return () => clearInterval(interval)
    }, [loadSensorData, syncControlStates])

  useEffect(() => {
    if (!hasMqttConfig) {
      return
    }

    const client = mqtt.connect(mqttUrl, {
      username: adafruitUsername,
      password: adafruitKey,
      reconnectPeriod: 3000,
      connectTimeout: 10000,
      clean: true,
    })

    mqttClientRef.current = client

    client.on('connect', () => {
      setMqttStatus('connected')
      setMqttError(null)
      client.subscribe([temperatureFeed, soilFeed], { qos: 1 }, (subscribeError) => {
        if (subscribeError) {
          setMqttError(subscribeError.message)
        }
      })
      void syncControlStates()
    })

    client.on('reconnect', () => {
      setMqttStatus('connecting')
    })

    client.on('close', () => {
      setMqttStatus('disconnected')
    })

    client.on('error', (eventError) => {
      setMqttStatus('error')
      setMqttError(eventError.message)
    })

    client.on('message', (topic, payload) => {
      const controlKey = keyByFeed[topic]
      if (!controlKey) {
        return
      }

      const value = payload.toString().trim()
      const enabled = value === '1'

      setControls((prev) => ({ ...prev, [controlKey]: enabled }))
      setControlPending((prev) => ({ ...prev, [controlKey]: false }))
    })

    return () => {
      client.end(true)
      mqttClientRef.current = null
    }
  }, [
    adafruitKey,
    adafruitUsername,
    hasMqttConfig,
    keyByFeed,
    mqttUrl,
    soilFeed,
    temperatureFeed,
  ])

  const publishControl = useCallback(
    (key: ControlKey) => {
      const client = mqttClientRef.current
      if (!client || mqttStatus !== 'connected') {
        return
      }

      const nextValue = controls[key] ? '0' : '1'
      const nextEnabled = nextValue === '1'

      setControlPending((prev) => ({ ...prev, [key]: true }))
      setControls((prev) => ({ ...prev, [key]: nextEnabled }))

      client.publish(feedByKey[key], nextValue, { qos: 1 }, (publishError) => {
        if (publishError) {
          setMqttError(publishError.message)
          setControlPending((prev) => ({ ...prev, [key]: false }))
          setControls((prev) => ({ ...prev, [key]: !nextEnabled }))
        }
      })
    },
    [controls, feedByKey, mqttStatus],
  )

  const latest = useMemo(
    () => (readings.length > 0 ? readings[readings.length - 1] : null),
    [readings],
  )

  const handleRefresh = useCallback(() => {
    void loadSensorData()
    void syncControlStates()
  }, [loadSensorData, syncControlStates])

  return (
    <main className="dashboard">
      <section className="panel">
        <header className="panel-header">
          <div>
            <h1>ESP Farm Dashboard</h1>
            <p>Live sensor trends from Supabase</p>
          </div>
          <button className="refresh-button" onClick={handleRefresh}>
            Refresh
          </button>
        </header>

        <section className="controls-panel">
          <div className="controls-title-row">
            <h2>Device Controls</h2>
            <span className={`mqtt-status ${mqttStatus}`}>MQTT: {mqttStatus}</span>
          </div>

          {!hasMqttConfig && (
            <p className="status error">
              Missing MQTT env vars. Set `VITE_ADAFRUIT_USERNAME` and `VITE_ADAFRUIT_KEY`.
            </p>
          )}

          {mqttError && <p className="status error">MQTT error: {mqttError}</p>}

          <div className="controls-grid">
            <ControlCard
              title="Temperature Switch"
              enabled={controls.temperature}
              pending={controlPending.temperature || mqttStatus !== 'connected'}
              onToggle={() => publishControl('temperature')}
            />
            <ControlCard
              title="Soil Switch"
              enabled={controls.soil}
              pending={controlPending.soil || mqttStatus !== 'connected'}
              onToggle={() => publishControl('soil')}
            />
          </div>
        </section>

        {latest && (
          <div className="summary-row">
            <p>Updated: {new Date(latest.createdAt).toLocaleString()}</p>
            <p>{readings.length} points loaded</p>
          </div>
        )}

        {loading && <p className="status">Loading sensor data...</p>}

        {!loading && error && (
          <p className="status error">Failed to load data: {error}</p>
        )}

        {!error && readings.length > 0 && (
          <div className="charts-grid">
            {METRICS.map((metric) => (
              <MetricChart key={metric.valueKey} data={readings} metric={metric} />
            ))}
          </div>
        )}

        {!loading && !error && readings.length === 0 && (
          <p className="status">Click refresh to load sensor data.</p>
        )}
      </section>
    </main>
  )
}

export default App
