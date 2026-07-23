import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  Bot,
  CalendarPlus,
  CloudSun,
  Euro,
  Plus,
  ReceiptText,
  RefreshCw,
  Send,
  Shirt,
  ShoppingBasket,
  Utensils,
} from "lucide-react";
import {
  addGrocery,
  askAssistant,
  addCalendarSource,
  addReceiptText,
  addScheduleItem,
  addWardrobeBulk,
  addWardrobeItem,
  API_BASE,
  deleteCalendarSource,
  deleteGrocery,
  deleteReceipt,
  deleteScheduleItem,
  deleteWardrobeItem,
  getAppleCalendarStatus,
  getBudgetStatus,
  getCalendarSources,
  getDailyBriefing,
  getExpenses,
  getGroceryExpiry,
  getGroceries,
  getLlmStatus,
  getOcrStatus,
  getReceipts,
  getSchedule,
  getWardrobe,
  processReceiptText,
  scanReceiptPhoto,
  syncCalendar,
  uploadWardrobePhoto,
} from "./api";
import "./styles.css";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function currentMonth() {
  return new Date().toISOString().slice(0, 7);
}

function dateTimeLocal(hour, minute) {
  const day = todayIso();
  return `${day}T${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function App() {
  const [briefing, setBriefing] = useState(null);
  const [groceries, setGroceries] = useState([]);
  const [wardrobe, setWardrobe] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [calendarSources, setCalendarSources] = useState([]);
  const [appleCalendar, setAppleCalendar] = useState(null);
  const [expenses, setExpenses] = useState(null);
  const [budget, setBudget] = useState(null);
  const [ocr, setOcr] = useState(null);
  const [llm, setLlm] = useState(null);
  const [expiry, setExpiry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [assistantQuestion, setAssistantQuestion] = useState("");
  const [assistantAnswer, setAssistantAnswer] = useState(null);
  const [assistantLoading, setAssistantLoading] = useState(false);

  const [groceryForm, setGroceryForm] = useState({
    name: "",
    category: "protein",
    quantity: "1 item",
    expires_on: "",
    store: "Aldi",
    price: "",
  });
  const [wardrobeForm, setWardrobeForm] = useState({
    name: "",
    item_type: "top",
    color: "",
    style: "casual",
    warmth: 1,
    rain_ready: false,
    sport_ready: false,
    formality: "casual",
    file: null,
  });
  const [wardrobeBulkText, setWardrobeBulkText] = useState("");
  const [scheduleForm, setScheduleForm] = useState({
    title: "",
    starts_at: dateTimeLocal(10, 0),
    ends_at: dateTimeLocal(12, 0),
    location: "TU Dresden",
    activity_type: "lecture",
    near_store: "",
  });
  const [receiptForm, setReceiptForm] = useState({
    store: "Aldi",
    purchased_on: todayIso(),
    raw_text: "",
  });
  const [receiptPhotoForm, setReceiptPhotoForm] = useState({
    store: "Aldi",
    purchased_on: todayIso(),
    file: null,
  });
  const [receiptCorrectionForm, setReceiptCorrectionForm] = useState({
    receipt_id: "",
    raw_text: "",
  });
  const [calendarSourceForm, setCalendarSourceForm] = useState({
    name: "Apple Calendar",
  });

  async function loadData() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const [
        briefingData,
        groceriesData,
        wardrobeData,
        scheduleData,
        receiptsData,
        calendarSourcesData,
        appleCalendarData,
        expensesData,
        budgetData,
        ocrData,
        llmData,
        expiryData,
      ] = await Promise.all([
        getDailyBriefing(),
        getGroceries(),
        getWardrobe(),
        getSchedule(),
        getReceipts(),
        getCalendarSources(),
        getAppleCalendarStatus(),
        getExpenses(currentMonth()),
        getBudgetStatus(currentMonth()),
        getOcrStatus(),
        getLlmStatus(),
        getGroceryExpiry(),
      ]);

      setBriefing(briefingData);
      setGroceries(groceriesData);
      setWardrobe(wardrobeData);
      setSchedule(scheduleData);
      setReceipts(receiptsData);
      setCalendarSources(calendarSourcesData);
      setAppleCalendar(appleCalendarData);
      setExpenses(expensesData);
      setBudget(budgetData);
      setOcr(ocrData);
      setLlm(llmData);
      setExpiry(expiryData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const budgetTone = useMemo(() => {
    if (!budget) return "neutral";
    if (budget.status === "over_budget") return "danger";
    if (budget.status === "near_limit") return "warning";
    return "good";
  }, [budget]);

  const wardrobeCoverage = useMemo(() => {
    const required = ["jacket", "top", "bottom", "shoes", "sport"];
    const counts = wardrobe.reduce((acc, item) => {
      acc[item.item_type] = (acc[item.item_type] || 0) + 1;
      return acc;
    }, {});
    return required.map((type) => ({
      type,
      count: counts[type] || 0,
      ready: (counts[type] || 0) > 0,
    }));
  }, [wardrobe]);

  async function handleGrocerySubmit(event) {
    event.preventDefault();
    await addGrocery({
      ...groceryForm,
      expires_on: groceryForm.expires_on || null,
      price: groceryForm.price ? Number(groceryForm.price) : null,
    });
    setGroceryForm({ ...groceryForm, name: "", price: "", expires_on: "" });
    loadData();
  }

  async function handleWardrobeSubmit(event) {
    event.preventDefault();
    if (wardrobeForm.file) {
      await uploadWardrobePhoto({
        ...wardrobeForm,
        warmth: Number(wardrobeForm.warmth),
      });
    } else {
      const { file, ...payload } = wardrobeForm;
      await addWardrobeItem({
        ...payload,
        warmth: Number(payload.warmth),
      });
    }
    setWardrobeForm({ ...wardrobeForm, name: "", color: "", file: null });
    loadData();
  }

  async function handleWardrobeBulkSubmit(event) {
    event.preventDefault();
    const items = wardrobeBulkText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map(parseWardrobeLine);
    if (!items.length) {
      setError("Add at least one wardrobe line.");
      return;
    }
    await addWardrobeBulk(items);
    setWardrobeBulkText("");
    setNotice(`${items.length} wardrobe item(s) added.`);
    loadData();
  }

  async function handleScheduleSubmit(event) {
    event.preventDefault();
    await addScheduleItem({
      ...scheduleForm,
      near_store: scheduleForm.near_store || null,
    });
    setScheduleForm({ ...scheduleForm, title: "", near_store: "" });
    loadData();
  }

  async function handleReceiptSubmit(event) {
    event.preventDefault();
    await addReceiptText(receiptForm);
    setReceiptForm({ ...receiptForm, raw_text: "" });
    loadData();
  }

  async function handleReceiptPhotoSubmit(event) {
    event.preventDefault();
    if (!receiptPhotoForm.file) {
      setError("Choose a receipt photo first.");
      return;
    }
    const receipt = await scanReceiptPhoto(receiptPhotoForm);
    setReceiptPhotoForm({ ...receiptPhotoForm, file: null });
    setNotice(
      receipt.status === "uploaded_needs_ocr"
        ? "Receipt photo saved. OCR is waiting for Tesseract, so paste corrected text below."
        : `Receipt scanned: ${receipt.items.length} item(s) found.`
    );
    loadData();
  }

  async function handleReceiptCorrectionSubmit(event) {
    event.preventDefault();
    await processReceiptText(receiptCorrectionForm.receipt_id, receiptCorrectionForm.raw_text);
    setReceiptCorrectionForm({ receipt_id: "", raw_text: "" });
    setNotice("Receipt text processed and groceries/expenses updated.");
    loadData();
  }

  async function handleCalendarSourceSubmit(event) {
    event.preventDefault();
    await addCalendarSource({
      name: calendarSourceForm.name,
      source_type: "apple_caldav",
      value: "default",
    });
    const result = await syncCalendar();
    setNotice(`Calendar sync: ${result.imported} added, ${result.updated} updated, ${result.skipped} skipped.`);
    loadData();
  }

  async function handleCalendarSync() {
    const result = await syncCalendar();
    setNotice(`Calendar sync: ${result.imported} added, ${result.updated} updated, ${result.skipped} skipped.`);
    loadData();
  }

  async function handleDelete(action, successMessage) {
    await action();
    setNotice(successMessage);
    loadData();
  }

  async function handleAssistantSubmit(event) {
    event.preventDefault();
    if (!assistantQuestion.trim()) return;
    setAssistantLoading(true);
    setError("");
    try {
      const result = await askAssistant(assistantQuestion);
      setAssistantAnswer(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setAssistantLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Student Life Agent</p>
          <h1>Jarvis</h1>
        </div>
        <button className="icon-button" onClick={loadData} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </header>

      {error && <div className="banner danger">Backend error: {error}</div>}
      {notice && <div className="banner">{notice}</div>}
      {loading && <div className="banner">Loading Jarvis data...</div>}

      <section className="assistant-console">
        <div className="assistant-copy">
          <div className="panel-title">
            <Bot size={20} />
            <h2>Ask Jarvis</h2>
          </div>
          <p>Test the question engine that Alexa will use later.</p>
        </div>
        <form onSubmit={handleAssistantSubmit} className="assistant-form">
          <input
            placeholder="Ask: What should I wear today?"
            value={assistantQuestion}
            onChange={(e) => setAssistantQuestion(e.target.value)}
          />
          <button className="primary-button" type="submit" disabled={assistantLoading}>
            <Send size={16} /> Ask
          </button>
        </form>
        {assistantAnswer && (
          <div className="assistant-answer">
            <span>{assistantAnswer.intent}</span>
            <p>{assistantAnswer.answer}</p>
            <div className="assistant-suggestions">
              {assistantAnswer.suggestions.map((suggestion) => (
                <button
                  className="secondary-button"
                  type="button"
                  key={suggestion}
                  onClick={() => setAssistantQuestion(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="overview-grid">
        <Panel title="Today" icon={<CloudSun size={18} />}>
          {briefing && (
            <>
              <p className="lead">{briefing.greeting}</p>
              <div className="weather-line">
                <strong>{briefing.weather.temperature_c.toFixed(1)}C</strong>
                <span>{briefing.weather.condition}</span>
                <span>{briefing.weather.precipitation_probability}% rain</span>
                <span>{briefing.weather.wind_kmh.toFixed(1)} km/h wind</span>
              </div>
              <List items={briefing.schedule} empty="No schedule items yet." />
            </>
          )}
        </Panel>

        <Panel title="Outfit" icon={<Shirt size={18} />}>
          {briefing?.outfit_details?.length ? (
            <div className="outfit-detail-list">
              {briefing.outfit_details.map((item, index) => (
                <article className="outfit-choice" key={`${item.name}-${index}`}>
                  {item.image_url ? (
                    <img src={`${API_BASE}${item.image_url}`} alt={item.name} />
                  ) : (
                    <div className="outfit-placeholder"><Shirt size={22} /></div>
                  )}
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.item_type}{item.color ? ` - ${item.color}` : ""}{item.style ? ` - ${item.style}` : ""}</span>
                    <p>{item.reason}</p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <List items={briefing?.outfit || []} empty="Add wardrobe items to unlock outfit planning." />
          )}
        </Panel>

        <Panel title="Meals" icon={<Utensils size={18} />}>
          {briefing && (
            briefing.meal_details?.length ? (
              <div className="meal-detail-list">
                {briefing.meal_details.map((item) => (
                  <article className="meal-card" key={item.meal}>
                    <div className="meal-card-header">
                      <span>{item.meal}</span>
                      <strong>{item.name}</strong>
                    </div>
                    <div className="meal-meta">
                      <span>{item.prep_minutes} min</span>
                      <span>{item.focus}</span>
                    </div>
                    <p>{item.reason}</p>
                    {item.ingredients.length > 0 && (
                      <div className="ingredient-row">
                        {item.ingredients.map((ingredient) => (
                          <span key={ingredient}>{ingredient}</span>
                        ))}
                      </div>
                    )}
                    {item.budget_note && <small>{item.budget_note}</small>}
                  </article>
                ))}
              </div>
            ) : (
              <div className="meal-grid">
                {Object.entries(briefing.meals).map(([meal, value]) => (
                  <div className="meal-row" key={meal}>
                    <span>{meal}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
            )
          )}
        </Panel>

        <Panel title="Alerts" icon={<AlertTriangle size={18} />}>
          <List items={briefing?.alerts || []} empty="No alerts for now." />
        </Panel>
      </section>

      <section className="metrics-row">
        <Metric
          title="Monthly Spend"
          value={expenses ? `${expenses.total.toFixed(2)} EUR` : "-"}
          detail={expenses?.suggestions?.[0] || "No receipt spending tracked."}
          icon={<Euro size={18} />}
        />
        <Metric
          title="Budget"
          value={budget ? `${budget.remaining.toFixed(2)} EUR left` : "-"}
          detail={budget?.message || "Budget status unavailable."}
          icon={<ShoppingBasket size={18} />}
          tone={budgetTone}
        />
        <Metric
          title="OCR"
          value={ocr?.available ? "Ready" : "Waiting"}
          detail={ocr?.message || "Checking OCR status."}
          icon={<ReceiptText size={18} />}
        />
        <Metric
          title="AI Reasoning"
          value={llm?.available ? "Enabled" : "Local"}
          detail={llm?.message || "Checking AI status."}
          icon={<Bot size={18} />}
          tone={llm?.available ? "good" : "neutral"}
        />
      </section>

      <section className="pantry-dashboard">
        <Panel title="Pantry Expiry" icon={<AlertTriangle size={18} />}>
          {expiry && (
            <>
              <div className="expiry-grid">
                <ExpiryBucket title="Expired" items={expiry.expired} tone="danger" />
                <ExpiryBucket title="Today" items={expiry.today} tone="warning" />
                <ExpiryBucket title="Soon" items={expiry.soon} tone="warning" />
                <ExpiryBucket title="Unknown" items={expiry.unknown} />
              </div>
              <List items={expiry.suggestions} empty="No pantry suggestions yet." />
            </>
          )}
        </Panel>
      </section>

      <section className="work-grid">
        <Panel title="Groceries" icon={<ShoppingBasket size={18} />}>
          <form onSubmit={handleGrocerySubmit} className="form-grid compact">
            <input required placeholder="Name" value={groceryForm.name} onChange={(e) => setGroceryForm({ ...groceryForm, name: e.target.value })} />
            <select value={groceryForm.category} onChange={(e) => setGroceryForm({ ...groceryForm, category: e.target.value })}>
              <option>protein</option>
              <option>dairy</option>
              <option>carb</option>
              <option>vegetable</option>
              <option>fruit</option>
              <option>snack</option>
              <option>other</option>
            </select>
            <input required placeholder="Quantity" value={groceryForm.quantity} onChange={(e) => setGroceryForm({ ...groceryForm, quantity: e.target.value })} />
            <input type="date" value={groceryForm.expires_on} onChange={(e) => setGroceryForm({ ...groceryForm, expires_on: e.target.value })} />
            <input placeholder="Store" value={groceryForm.store} onChange={(e) => setGroceryForm({ ...groceryForm, store: e.target.value })} />
            <input type="number" step="0.01" placeholder="Price" value={groceryForm.price} onChange={(e) => setGroceryForm({ ...groceryForm, price: e.target.value })} />
            <button className="primary-button" type="submit"><Plus size={16} /> Add</button>
          </form>
          <DataList
            rows={groceries.slice(0, 8)}
            render={(item) => `${item.name} - ${item.quantity}${item.expires_on ? ` - expires ${item.expires_on}` : ""}`}
            onDelete={(item) => handleDelete(() => deleteGrocery(item.id), "Grocery removed.")}
          />
        </Panel>

        <Panel title="Wardrobe" icon={<Shirt size={18} />}>
          <div className="coverage-row">
            {wardrobeCoverage.map((item) => (
              <span className={item.ready ? "coverage-chip ready" : "coverage-chip"} key={item.type}>
                {item.type}: {item.count}
              </span>
            ))}
          </div>
          <form onSubmit={handleWardrobeSubmit} className="form-grid compact">
            <input required placeholder="Item name" value={wardrobeForm.name} onChange={(e) => setWardrobeForm({ ...wardrobeForm, name: e.target.value })} />
            <select value={wardrobeForm.item_type} onChange={(e) => setWardrobeForm({ ...wardrobeForm, item_type: e.target.value })}>
              <option>jacket</option>
              <option>top</option>
              <option>bottom</option>
              <option>shoes</option>
              <option>sport</option>
            </select>
            <input required placeholder="Color" value={wardrobeForm.color} onChange={(e) => setWardrobeForm({ ...wardrobeForm, color: e.target.value })} />
            <input placeholder="Style" value={wardrobeForm.style} onChange={(e) => setWardrobeForm({ ...wardrobeForm, style: e.target.value })} />
            <input type="number" min="1" max="5" value={wardrobeForm.warmth} onChange={(e) => setWardrobeForm({ ...wardrobeForm, warmth: e.target.value })} />
            <label className="check"><input type="checkbox" checked={wardrobeForm.rain_ready} onChange={(e) => setWardrobeForm({ ...wardrobeForm, rain_ready: e.target.checked })} /> Rain</label>
            <label className="check"><input type="checkbox" checked={wardrobeForm.sport_ready} onChange={(e) => setWardrobeForm({ ...wardrobeForm, sport_ready: e.target.checked })} /> Sport</label>
            <input type="file" accept="image/*" onChange={(e) => setWardrobeForm({ ...wardrobeForm, file: e.target.files?.[0] || null })} />
            <button className="primary-button" type="submit"><Plus size={16} /> Add</button>
          </form>
          <form onSubmit={handleWardrobeBulkSubmit} className="bulk-wardrobe-form">
            <textarea
              placeholder={"Bulk add without photos:\nblack rain jacket,jacket,black,casual minimal,4,true,false,casual\nwhite sneakers,shoes,white,casual,1,false,false,casual"}
              value={wardrobeBulkText}
              onChange={(e) => setWardrobeBulkText(e.target.value)}
            />
            <button className="secondary-button" type="submit">Add Bulk Items</button>
          </form>
          <div className="wardrobe-gallery">
            {wardrobe.slice(0, 8).map((item) => (
              <article className="wardrobe-tile" key={item.id}>
                {item.image_url ? (
                  <img src={`${API_BASE}${item.image_url}`} alt={item.name} />
                ) : (
                  <div className="wardrobe-placeholder"><Shirt size={24} /></div>
                )}
                <div>
                  <strong>{item.name}</strong>
                  <span>{item.color} - {item.style}</span>
                </div>
                <button className="danger-button" type="button" onClick={() => handleDelete(() => deleteWardrobeItem(item.id), "Wardrobe item removed.")}>Remove</button>
              </article>
            ))}
          </div>
        </Panel>

        <Panel title="Schedule" icon={<CalendarPlus size={18} />}>
          <form onSubmit={handleCalendarSourceSubmit} className="apple-calendar-form">
            <input required placeholder="Apple Calendar source name" value={calendarSourceForm.name} onChange={(e) => setCalendarSourceForm({ ...calendarSourceForm, name: e.target.value })} />
            <button className="primary-button" type="submit"><CalendarPlus size={16} /> Link Apple</button>
          </form>
          <p className={`config-note ${appleCalendar?.configured ? "good-text" : "warning-text"}`}>
            {appleCalendar?.message || "Checking Apple Calendar configuration..."}
          </p>
          <div className="source-row">
            <button className="secondary-button" type="button" onClick={handleCalendarSync}>Sync saved calendars</button>
            <span>{calendarSources.length} saved source(s)</span>
          </div>
          <DataList
            rows={calendarSources.filter((source) => source.active).slice(0, 4)}
            render={(source) => `${source.name} - ${source.source_type}${source.last_synced_at ? ` - synced ${source.last_synced_at}` : ""}`}
            onDelete={(source) => handleDelete(() => deleteCalendarSource(source.id), "Calendar source disabled.")}
          />
          <form onSubmit={handleScheduleSubmit} className="form-grid compact">
            <input required placeholder="Title" value={scheduleForm.title} onChange={(e) => setScheduleForm({ ...scheduleForm, title: e.target.value })} />
            <select value={scheduleForm.activity_type} onChange={(e) => setScheduleForm({ ...scheduleForm, activity_type: e.target.value })}>
              <option>lecture</option>
              <option>football</option>
              <option>gym</option>
              <option>study</option>
              <option>errand</option>
            </select>
            <input type="datetime-local" value={scheduleForm.starts_at} onChange={(e) => setScheduleForm({ ...scheduleForm, starts_at: e.target.value })} />
            <input type="datetime-local" value={scheduleForm.ends_at} onChange={(e) => setScheduleForm({ ...scheduleForm, ends_at: e.target.value })} />
            <input placeholder="Location" value={scheduleForm.location} onChange={(e) => setScheduleForm({ ...scheduleForm, location: e.target.value })} />
            <input placeholder="Nearby store" value={scheduleForm.near_store} onChange={(e) => setScheduleForm({ ...scheduleForm, near_store: e.target.value })} />
            <button className="primary-button" type="submit"><Plus size={16} /> Add</button>
          </form>
          <DataList
            rows={schedule.slice(0, 8)}
            render={(item) => `${item.title} - ${item.starts_at.slice(11, 16)}-${item.ends_at.slice(11, 16)}`}
            onDelete={(item) => handleDelete(() => deleteScheduleItem(item.id), "Schedule item removed.")}
          />
        </Panel>

        <Panel title="Receipt Text" icon={<ReceiptText size={18} />}>
          <form onSubmit={handleReceiptPhotoSubmit} className="receipt-form">
            <div className="form-row">
              <input required placeholder="Store" value={receiptPhotoForm.store} onChange={(e) => setReceiptPhotoForm({ ...receiptPhotoForm, store: e.target.value })} />
              <input type="date" value={receiptPhotoForm.purchased_on} onChange={(e) => setReceiptPhotoForm({ ...receiptPhotoForm, purchased_on: e.target.value })} />
            </div>
            <div className="form-row">
              <input type="file" accept="image/*" onChange={(e) => setReceiptPhotoForm({ ...receiptPhotoForm, file: e.target.files?.[0] || null })} />
              <button className="primary-button" type="submit"><ReceiptText size={16} /> Scan Photo</button>
            </div>
          </form>
          <form onSubmit={handleReceiptSubmit} className="receipt-form">
            <div className="form-row">
              <input required placeholder="Store" value={receiptForm.store} onChange={(e) => setReceiptForm({ ...receiptForm, store: e.target.value })} />
              <input type="date" value={receiptForm.purchased_on} onChange={(e) => setReceiptForm({ ...receiptForm, purchased_on: e.target.value })} />
            </div>
            <textarea required placeholder={"Milk 1,09\nEggs 2,49\nTOTAL 3,58"} value={receiptForm.raw_text} onChange={(e) => setReceiptForm({ ...receiptForm, raw_text: e.target.value })} />
            <button className="primary-button" type="submit"><ReceiptText size={16} /> Process</button>
          </form>
          <form onSubmit={handleReceiptCorrectionSubmit} className="receipt-form">
            <div className="form-row">
              <select required value={receiptCorrectionForm.receipt_id} onChange={(e) => setReceiptCorrectionForm({ ...receiptCorrectionForm, receipt_id: e.target.value })}>
                <option value="">Receipt to correct</option>
                {receipts.map((receipt) => (
                  <option key={receipt.id} value={receipt.id}>
                    #{receipt.id} {receipt.store} - {receipt.status}
                  </option>
                ))}
              </select>
              <button className="secondary-button" type="submit">Apply Text</button>
            </div>
            <textarea required placeholder={"Paste OCR/corrected receipt text here"} value={receiptCorrectionForm.raw_text} onChange={(e) => setReceiptCorrectionForm({ ...receiptCorrectionForm, raw_text: e.target.value })} />
          </form>
          <div className="receipt-list">
            {receipts.slice(0, 6).map((item) => (
              <article className="receipt-row" key={item.id}>
                {item.image_url && <img src={`${API_BASE}${item.image_url}`} alt={`${item.store} receipt`} />}
                <div>
                  <strong>{item.store} - {item.total.toFixed(2)} EUR</strong>
                  <span>{item.purchased_on} - {item.status} - {item.items.length} item(s)</span>
                </div>
                <button className="danger-button" type="button" onClick={() => handleDelete(() => deleteReceipt(item.id), "Receipt removed.")}>Remove</button>
              </article>
            ))}
          </div>
        </Panel>
      </section>
    </main>
  );
}

function Panel({ title, icon, children }) {
  return (
    <section className="panel">
      <div className="panel-title">
        {icon}
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ title, value, detail, icon, tone = "neutral" }) {
  return (
    <section className={`metric ${tone}`}>
      <div className="metric-head">
        {icon}
        <span>{title}</span>
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </section>
  );
}

function List({ items, empty }) {
  if (!items.length) return <p className="muted">{empty}</p>;
  return (
    <ul className="clean-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

function ExpiryBucket({ title, items, tone = "neutral" }) {
  return (
    <article className={`expiry-bucket ${tone}`}>
      <span>{title}</span>
      <strong>{items.length}</strong>
      <small>{items.slice(0, 2).map((item) => item.name).join(", ") || "None"}</small>
    </article>
  );
}

function DataList({ rows, render, onDelete }) {
  if (!rows.length) return <p className="muted">No entries yet.</p>;
  return (
    <ul className="data-list">
      {rows.map((row) => (
        <li key={row.id}>
          <span>{render(row)}</span>
          {onDelete && (
            <button className="danger-button" type="button" onClick={() => onDelete(row)}>
              Remove
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}

function parseWardrobeLine(line) {
  const [name, itemType, color, style, warmth, rainReady, sportReady, formality] = line
    .split(",")
    .map((part) => part.trim());
  return {
    name,
    item_type: itemType || "top",
    color: color || "unknown",
    style: style || "casual",
    warmth: Number(warmth || 1),
    rain_ready: ["true", "yes", "rain"].includes((rainReady || "").toLowerCase()),
    sport_ready: ["true", "yes", "sport"].includes((sportReady || "").toLowerCase()),
    formality: formality || "casual",
  };
}

createRoot(document.getElementById("root")).render(<App />);
