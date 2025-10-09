// UI logic for single-page app: tabs, forms, RT search, tables, filters
// Backend API base URL (adjust if running on different host/port)
const API_BASE = 'http://127.0.0.1:8000';

const API = {
  auth: {
    login: `${API_BASE}/auth/login`, // POST
  },
  books: {
    search: `${API_BASE}/books/`, // GET ?search=...
    create: `${API_BASE}/books/`, // POST
    uploadExcel: `${API_BASE}/books/upload-excel`, // POST (multipart/form-data)
  },
  categories: {
    list: `${API_BASE}/books/categories`, // GET
  },
  students: {
    list: `${API_BASE}/students/`, // GET
    create: `${API_BASE}/students/`, // POST
    delete: (id) => `${API_BASE}/students/${id}`, // DELETE
    uploadExcel: `${API_BASE}/students/upload-excel`, // POST (multipart/form-data)
  },
  loans: {
    list: `${API_BASE}/loans/`, // GET with optional ?returned=bool&student_id=&book_id=
    create: `${API_BASE}/loans/`, // POST
    return: (id) => `${API_BASE}/loans/${id}/return`, // POST
    delete: (id) => `${API_BASE}/loans/${id}`, // DELETE
  },
};

// ========================= Demo Mode (Frontend-only Data) =========================
// Set to true to run entirely on the frontend with seeded sample data
// Change to false to use the real backend API
const DEMO_MODE = false;

const DEMO_KEY = 'library_demo_data_v1';

function demoGetState() {
  try {
    const raw = localStorage.getItem(DEMO_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function demoSetState(state) {
  localStorage.setItem(DEMO_KEY, JSON.stringify(state));
}

function randomChoice(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function randInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }

// Helpers to work with Persian (Jalali) calendar using Intl
const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
function p2n(str){
  return Number(String(str ?? '').replace(/[۰-۹]/g, d => String(PERSIAN_DIGITS.indexOf(d))));
}
function getJalaliParts(date){
  try {
    const parts = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { year:'numeric', month:'numeric', day:'numeric' }).formatToParts(date);
    const get = (t) => parts.find(p => p.type === t)?.value;
    return { y: p2n(get('year')), m: p2n(get('month')), d: p2n(get('day')) };
  } catch {
    // Fallback: not expected in modern browsers
    return { y: date.getFullYear(), m: date.getMonth()+1, d: date.getDate() };
  }
}
function findDateForJalali(y, m, d){
  // Search around Sep-Oct for the requested Jalali date (Mehr ~ month 7)
  const start = new Date(new Date().getFullYear(), 8, 1); // Sep 1 (month index 8)
  for (let i = 0; i < 90; i++) {
    const cand = new Date(start);
    cand.setDate(start.getDate() + i);
    const jp = getJalaliParts(cand);
    if (jp.y === y && jp.m === m && jp.d === d) return cand;
  }
  return new Date();
}

function seedDemoDataIfEmpty() {
  let s = demoGetState();
  if (s) return s;

  const grades = ['دهم','یازدهم','دوازدهم'];
  const majors = ['الکترونیک','الکتروتکنیک','مکاترونیک','عمران','شبکه'];
  const firstNames = ['علی','محمد','حسین','رضا','امیر','حامد','مهدی','سینا','پوریا','محمدرضا','یاسین','امیرحسین','آرمین','مبین','دانیال','سجاد','نیما','پارسا','اشکان','کیان'];
  const lastNames = ['رضایی','محمدی','حسینی','احمدی','کریمی','مرادی','جعفری','حیدری','موسوی','هاشمی','قاسمی','پورباقر','اکبری','امینی','امیری','نوری','کاظمی','حسنی','رهنما','صادقی'];

  // Categories (genres)
  const genreNames = ['رمان','علمی','تاریخی','مذهبی','کودک و نوجوان','تکنولوژی','شعر','فلسفه','روانشناسی','هنر'];
  const categories = genreNames.map((name, idx) => ({ id: idx + 1, name }));

  // Books: around 50 (5 per genre)
  const books = [];
  let bookId = 1;
  for (const cat of categories) {
    const count = 5; // fixed 5 per genre → 50 total for 10 genres
    for (let i = 1; i <= count; i++) {
      books.push({ id: bookId++, name: `${cat.name} - کتاب ${i}`, category_id: cat.id });
    }
  }

  // Students: per grade at least 10, and per major 3 per grade → 15 per grade (5 majors x 3)
  const students = [];
  let studentId = 1;
  for (const g of grades) {
    for (const m of majors) {
      for (let i = 0; i < 3; i++) {
        const fn = randomChoice(firstNames);
        const ln = randomChoice(lastNames);
        students.push({ id: studentId++, full_name: `${fn} ${ln}`, grade: `${g} - ${m}` });
      }
    }
  }

  // Loans: create ~30 mixed records
  const loans = [];
  let loanId = 1;
  const jy = getJalaliParts(new Date()).y; // current Jalali year
  for (let i = 0; i < 30; i++) {
    const stu = randomChoice(students);
    const bk = randomChoice(books);
    // Loan dates strictly in Mehr 1..9
    const day = randInt(1, 9);
    const loanDate = findDateForJalali(jy, 7, day); // month 7 = Mehr
    const dueDate = new Date(loanDate);
    dueDate.setDate(loanDate.getDate() + randInt(7, 21));
    const returned = Math.random() < 0.7; // 70% returned
    let returned_at = null;
    if (returned) {
      const ret = new Date(loanDate);
      ret.setDate(loanDate.getDate() + randInt(1, 60)); // return within max 60 days
      returned_at = ret.toISOString();
    }
    loans.push({
      id: loanId++, student_id: stu.id, book_id: bk.id,
      loan_date: loanDate.toISOString(),
      due_date: dueDate.toISOString(),
      returned, returned_at
    });
  }

  s = {
    nextIds: { category: categories.length + 1, book: books.length + 1, student: students.length + 1, loan: loans.length + 1 },
    categories, books, students, loans,
  };
  demoSetState(s);
  return s;
}

function withRelations(state, loan) {
  return {
    ...loan,
    student: state.students.find(s => s.id === loan.student_id) || null,
    book: state.books.find(b => b.id === loan.book_id) || null,
  };
}

async function mockFetch(url, options = {}) {
  // Ensure seed exists
  const state = seedDemoDataIfEmpty();
  const u = new URL(url);
  const path = u.pathname;
  const method = (options.method || 'GET').toUpperCase();
  const getBody = () => {
    if (!options.body) return null;
    try { return JSON.parse(options.body); } catch { return null; }
  };

  // Books categories
  if (path === '/books/categories' && method === 'GET') {
    return state.categories;
  }

  // Books search/create
  if (path === '/books/' && method === 'GET') {
    const q = (u.searchParams.get('search') || '').trim();
    const list = state.books.filter(b => !q || b.name.includes(q)).map(b => ({
      id: b.id,
      name: b.name,
      category: state.categories.find(c => c.id === b.category_id) || null,
    }));
    return list;
  }
  if (path === '/books/' && method === 'POST') {
    const body = getBody() || {};
    const id = state.nextIds.book++;
    const book = { id, name: body.name || '---', category_id: body.category_id || null };
    state.books.push(book);
    demoSetState(state);
    return { ...book };
  }

  // Students list/create/delete
  if (path === '/students/' && method === 'GET') {
    return state.students;
  }
  if (path === '/students/' && method === 'POST') {
    const body = getBody() || {};
    const id = state.nextIds.student++;
    const stu = { id, full_name: body.full_name || '---', grade: body.grade || '' };
    state.students.push(stu);
    demoSetState(state);
    return { ...stu };
  }
  if (path.startsWith('/students/') && method === 'DELETE') {
    const id = parseInt(path.split('/').pop(), 10);
    const idx = state.students.findIndex(s => s.id === id);
    if (idx >= 0) state.students.splice(idx, 1);
    // Also remove loans of that student for consistency
    for (let i = state.loans.length - 1; i >= 0; i--) if (state.loans[i].student_id === id) state.loans.splice(i, 1);
    demoSetState(state);
    return {};
  }

  // Loans list/create/delete/return
  if (path === '/loans/' && method === 'GET') {
    const returnedParam = u.searchParams.get('returned');
    let list = state.loans.slice();
    if (returnedParam === 'true') list = list.filter(l => !!l.returned);
    if (returnedParam === 'false') list = list.filter(l => !l.returned);
    return list.map(l => withRelations(state, l));
  }
  if (path === '/loans/' && method === 'POST') {
    const body = getBody() || {};
    const id = state.nextIds.loan++;
    const loan = {
      id,
      student_id: parseInt(body.student_id, 10),
      book_id: parseInt(body.book_id, 10),
      loan_date: new Date().toISOString(),
      due_date: body.due_date || null,
      returned: false,
      returned_at: null,
    };
    state.loans.push(loan);
    demoSetState(state);
    return withRelations(state, loan);
  }
  if (path.startsWith('/loans/') && method === 'DELETE') {
    const id = parseInt(path.split('/')[2], 10);
    const idx = state.loans.findIndex(l => l.id === id);
    if (idx >= 0) state.loans.splice(idx, 1);
    demoSetState(state);
    return {};
  }
  if (path.startsWith('/loans/') && path.endsWith('/return') && method === 'POST') {
    const id = parseInt(path.split('/')[2], 10);
    const l = state.loans.find(x => x.id === id);
    if (l) { l.returned = true; l.returned_at = new Date().toISOString(); }
    demoSetState(state);
    return withRelations(state, l);
  }

  // Unknown route in demo
  return {};
}

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function showToast(msg, type = 'info') {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  if (type === 'error') el.style.borderColor = '#8e0000';
  if (type === 'success') el.style.borderColor = '#1b5e20';
  clearTimeout(el._t);
  el._t = setTimeout(() => {
    el.classList.remove('show');
    el.style.borderColor = '';
  }, 2600);
}

function formatDateISO(d) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function formatDateHuman(d) {
  try {
    return new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium' }).format(d);
  } catch {
    return formatDateISO(d);
  }
}

function debounce(fn, wait = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

async function apiFetch(url, options) {
  try {
    // In demo mode, intercept and return mock data without network
    if (DEMO_MODE) {
      return await mockFetch(url, options);
    }

    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });

    // Handle 204 No Content (no body to parse)
    if (res.status === 204) {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return null;
    }

    const contentType = res.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await res.json() : await res.text();
    if (!res.ok) throw new Error((data && data.detail) || data || `HTTP ${res.status}`);
    return data;
  } catch (err) {
    showToast(String(err.message || err), 'error');
    throw err;
  }
}

function initTabs() {
  const buttons = $$('.tab');
  buttons.forEach((btn) =>
    btn.addEventListener('click', () => {
      buttons.forEach((b) => b.classList.remove('active'));
      $$('.tab-panel').forEach((p) => p.setAttribute('hidden', ''));
      btn.classList.add('active');
      const id = btn.dataset.tab;
      const panel = document.getElementById(id);
      panel.classList.add('active');
      panel.removeAttribute('hidden');
      // Lazy-load data for specific tabs when activated
      if (id === 'tab-reports') {
        // Ensure reports section is initialized and loaded
        if (typeof updateReports === 'function') updateReports();
      }
    })
  );
}

function initBookSearch() {
  const input = $('#book-search');
  const hiddenId = $('#book-id');
  const container = $('#book-search-results');

  function renderList(items) {
    container.innerHTML = '';
    const list = document.createElement('div');
    list.className = 'item-list';

    if (!items || items.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'نتیجه‌ای یافت نشد';
      list.appendChild(empty);
    } else {
      for (const it of items) {
        const row = document.createElement('div');
        row.className = 'item';
        const title = document.createElement('div');
        title.textContent = `${it.name || it.title || '---'}`;
        const meta = document.createElement('small');
        meta.style.color = '#b9b1a6';
        meta.textContent = it.category ? `دسته: ${it.category.name || it.category}` : '';
        row.appendChild(title);
        row.appendChild(meta);
        row.addEventListener('click', () => {
          input.value = it.name || it.title || '';
          hiddenId.value = it.id || it.book_id || '';
          container.innerHTML = '';
        });
        list.appendChild(row);
      }
    }
    container.appendChild(list);
  }

  const doSearch = debounce(async () => {
    const q = input.value.trim();
    if (!q) {
      container.innerHTML = '';
      hiddenId.value = '';
      return;
    }
    const url = `${API.books.search}?search=${encodeURIComponent(q)}`;
    try {
      const results = await apiFetch(url);
      renderList(Array.isArray(results) ? results : results.items || []);
    } catch (e) {
      // keep dropdown hidden on error
      container.innerHTML = '';
    }
  }, 250);

  input.addEventListener('input', doSearch);
  document.addEventListener('click', (e) => {
    if (!container.contains(e.target) && e.target !== input) container.innerHTML = '';
  });
}

function initDueDateCalculator() {
  const daysInput = $('#loan-days');
  const dueInput = $('#loan-due');

  function updateDue() {
    const days = parseInt(daysInput.value || '0', 10);
    const d = new Date();
    if (!isNaN(days) && days > 0) d.setDate(d.getDate() + days);
    dueInput.value = formatDateHuman(d);
    dueInput.dataset.iso = formatDateISO(d);
  }

  // Enforce default 7 days on load if empty/invalid
  daysInput.value = 7;
  daysInput.addEventListener('input', updateDue);
  updateDue();
}

async function loadCategories() {
  const select = $('#book-category');
  try {
    const categories = await apiFetch(API.categories.list);
    select.innerHTML = '<option value="">انتخاب دسته‌بندی...</option>';
    if (Array.isArray(categories) && categories.length > 0) {
      for (const cat of categories) {
        const option = document.createElement('option');
        option.value = cat.id;
        option.textContent = cat.name;
        if (cat.description) option.title = cat.description;
        select.appendChild(option);
      }
    } else {
      select.innerHTML = '<option value="">دسته‌بندی موجود نیست</option>';
      console.warn('No categories found');
    }
  } catch (e) {
    console.error('Failed to load categories:', e);
    select.innerHTML = '<option value="">خطا در بارگذاری - لطفاً Backend را راه‌اندازی کنید</option>';
  }
}

function initAddBookForm() {
  const form = $('#form-add-book');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const categoryId = fd.get('category');
    const payload = {
      name: fd.get('title'), // Backend expects 'name'
      category_id: categoryId ? parseInt(categoryId, 10) : null,
    };
    await apiFetch(API.books.create, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showToast('کتاب با موفقیت ثبت شد', 'success');
    form.reset();
    // Reload categories after reset
    await loadCategories();
  });
}

function initCreateLoanForm() {
  const form = $('#form-create-loan');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const bookId = $('#book-id').value;
    const studentIdInput = $('#loan-national-id').value.trim();
    const dueISO = $('#loan-due').dataset.iso;
    if (!bookId) return showToast('لطفاً کتاب را انتخاب کنید', 'error');
    if (!studentIdInput) return showToast('شناسه هنرجو را وارد کنید', 'error');

    // Backend expects student_id (integer), book_id (integer), and optional due_date
    const payload = { 
      book_id: parseInt(bookId, 10), 
      student_id: parseInt(studentIdInput, 10),
      due_date: dueISO ? `${dueISO}T00:00:00Z` : undefined
    };
    await apiFetch(API.loans.create, { method: 'POST', body: JSON.stringify(payload) });
    showToast('امانت ثبت شد', 'success');
    // refresh lists affected
    try { 
      await Promise.all([loadLoans(), loadStudents()]); 
      // refresh reports cache/view if open
      HISTORY_CACHE = [];
      if (document.getElementById('tab-reports')?.classList.contains('active')) {
        await updateReports();
      }
    } catch {}
    form.reset();
    $('#book-search-results').innerHTML = '';
    // recompute due date after reset
    $('#loan-days').value = 7; const evt = new Event('input'); $('#loan-days').dispatchEvent(evt);
  });
}

async function loadStudents() {
  const tbody = $('#students-table tbody');
  tbody.innerHTML = '';
  let data = [];
  try {
    const res = await apiFetch(API.students.list);
    data = Array.isArray(res) ? res : res.items || [];
  } catch (e) {
    // graceful fallback
    data = [];
  }
  for (const u of data) {
    const tr = document.createElement('tr');
    tr.dataset.id = u.id;
    tr.innerHTML = `
      <td>${u.full_name || '-'}</td>
      <td>${u.id || '-'}</td>
      <td>${u.grade || '-'}</td>
      <td>${u.major || '-'}</td>
      <td class="status"><span class="status-badge status-ok">عادی</span></td>
      <td><button class="btn danger btn-del" data-id="${u.id}">حذف</button></td>
    `;
    tbody.appendChild(tr);
  }
  // Attach delete handlers
  $$('#students-table .btn-del').forEach((btn) =>
    btn.addEventListener('click', async () => {
      const id = btn.dataset.id;
      try {
        await apiFetch(API.students.delete(id), { method: 'DELETE' });
        showToast('حذف شد', 'success');
        await loadStudents();
      } catch {}
    })
  );
  // After (re)load, compute overdue flags based on loans
  try { await markOverdueStudents(); } catch {}
}

async function markOverdueStudents() {
  try {
    const loans = await apiFetch(`${API.loans.list}?returned=false`);
    const items = Array.isArray(loans) ? loans : loans.items || [];
    const now = new Date();
    // Build set of student IDs who are overdue
    const overdueSet = new Set();
    for (const l of items) {
      const due = new Date(l.due_date || 0);
      if (isFinite(due.getTime()) && due < now) {
        const sid = l.student_id || (l.student && l.student.id);
        if (sid) overdueSet.add(String(sid));
      }
    }
    // Paint rows
    $$('#students-table tbody tr').forEach((tr) => {
      const sid = tr.children[1]?.textContent?.trim();
      const statusCell = tr.querySelector('.status');
      if (overdueSet.has(sid)) {
        tr.classList.add('overdue');
        statusCell.innerHTML = '<span class="status-badge status-late">تاخیر</span>';
      } else {
        tr.classList.remove('overdue');
        statusCell.innerHTML = '<span class="status-badge status-ok">عادی</span>';
      }
    });
  } catch (e) {
    // Ignore errors
  }
}

function initAddStudentForm() {
  const form = $('#form-add-student');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const payload = {
      first_name: fd.get('first_name'),
      last_name: fd.get('last_name'),
      grade: fd.get('grade'),
      major: fd.get('major'),
    };
    await apiFetch(API.students.create, { method: 'POST', body: JSON.stringify(payload) });
    showToast('هنرجو افزوده شد', 'success');
    await loadStudents();
    form.reset();
  });
}

async function loadLoans(filters = {}) {
  const tbody = $('#loans-table tbody');
  tbody.innerHTML = '';
  
  let data = [];
  try {
    const res = await apiFetch(API.loans.list);
    data = Array.isArray(res) ? res : res.items || [];
  } catch (e) {
    data = [];
  }
  
  // Client-side filtering by grade and major
  if (filters.grade || filters.major) {
    data = data.filter(l => {
      if (!l.student) return false;
      
      const studentGrade = (l.student.grade || '').trim().toLowerCase();
      const studentMajor = (l.student.major || '').trim().toLowerCase();
      
      let matchGrade = true;
      let matchMajor = true;
      
      if (filters.grade) {
        matchGrade = studentGrade === filters.grade.toLowerCase();
      }
      
      if (filters.major) {
        matchMajor = studentMajor === filters.major.toLowerCase();
      }
      
      return matchGrade && matchMajor;
    });
  }
  
  const now = new Date();
  
  if (data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--muted);">امانتی یافت نشد</td></tr>';
    return;
  }
  
  for (const l of data) {
    const tr = document.createElement('tr');
    const due = new Date(l.due_date || 0);
    const start = new Date(l.loan_date || 0);
    const returned = Boolean(l.returned);
    const isLate = !returned && isFinite(due.getTime()) && due < now;
    if (isLate) tr.classList.add('overdue');
    
    const studentName = l.student ? l.student.full_name : '-';
    const bookName = l.book ? l.book.name : '-';
    
    tr.innerHTML = `
      <td>${studentName}</td>
      <td>${bookName}</td>
      <td>${isFinite(start.getTime()) ? formatDateHuman(start) : '-'}</td>
      <td>${isFinite(due.getTime()) ? formatDateHuman(due) : '-'}</td>
      <td>${returned ? '<span class="status-badge status-ok">برگشته</span>' : (isLate ? '<span class="status-badge status-late">تاخیر</span>' : '<span class="status-badge status-ok">فعال</span>')}</td>
      <td><button class="btn danger btn-del-loan" data-id="${l.id}">حذف</button></td>
    `;
    tbody.appendChild(tr);
  }
  
  // Attach delete handlers
  $$('#loans-table .btn-del-loan').forEach((btn) =>
    btn.addEventListener('click', async () => {
      const id = btn.dataset.id;
      try {
        await apiFetch(API.loans.delete(id), { method: 'DELETE' });
        showToast('امانت حذف شد', 'success');
        // Re-apply current filters
        const currentGrade = $('#filter-grade').value;
        const currentMajor = $('#filter-major').value;
        await loadLoans({ grade: currentGrade, major: currentMajor });
        // refresh reports cache/view if open
        HISTORY_CACHE = [];
        if (document.getElementById('tab-reports')?.classList.contains('active')) {
          await updateReports();
        }
      } catch (e) {
        // Error already shown by apiFetch
      }
    })
  );
}

function initLoanFilters() {
  const grade = $('#filter-grade');
  const major = $('#filter-major');
  
  const apply = async () => {
    await loadLoans({ grade: grade.value, major: major.value });
  };
  
  grade.addEventListener('change', apply);
  major.addEventListener('change', apply);
}

// ========================= Reports (گزارشات) =========================
let HISTORY_CACHE = [];
let HISTORY_VIEW = [];

function splitName(fullName = '') {
  const parts = String(fullName || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return { first: '-', last: '-' };
  if (parts.length === 1) return { first: parts[0], last: '-' };
  const last = parts.pop();
  const first = parts.join(' ');
  return { first, last };
}

function parseGradeMajor(student = {}) {
  const grade = String(student.grade || '').trim();
  const major = String(student.major || '').trim();
  return { grade, major };
}

function daysBetween(a, b) {
  const ms = b.getTime() - a.getTime();
  if (!isFinite(ms)) return '-';
  return Math.max(0, Math.round(ms / (1000 * 60 * 60 * 24)));
}

async function ensureHistoryCache() {
  if (HISTORY_CACHE.length > 0) return HISTORY_CACHE;
  try {
    const res = await apiFetch(API.loans.list);
    const items = Array.isArray(res) ? res : (res.items || []);
    HISTORY_CACHE = items;
  } catch {
    HISTORY_CACHE = [];
  }
  return HISTORY_CACHE;
}

function applyReportFilters(items, { nameQ = '', grade = '', major = '' } = {}) {
  const q = String(nameQ || '').trim().toLowerCase();
  const g = String(grade || '').trim().toLowerCase();
  const m = String(major || '').trim().toLowerCase();

  return items.filter(l => {
    const stu = l.student || {};
    const { grade: sg, major: sm } = parseGradeMajor(stu);
    const fullName = (stu.full_name || '').toLowerCase();
    const nameOk = !q || fullName.includes(q);
    const gradeOk = !g || (sg || '').toLowerCase() === g;
    const majorOk = !m || (sm || '').toLowerCase() === m;
    return nameOk && gradeOk && majorOk;
  });
}

function mapHistoryRows(items) {
  const now = new Date();
  return items.map(l => {
    const stu = l.student || {};
    const { first, last } = splitName(stu.full_name || '');
    const { grade, major } = parseGradeMajor(stu);
    const loanAt = new Date(l.loan_date || 0);
    const dueAt = new Date(l.due_date || 0);
    const retRaw = l.returned_at || l.return_date || l.returnDate || null;
    const retAt = retRaw ? new Date(retRaw) : null;
    const isReturned = Boolean(l.returned || (retAt && isFinite(retAt.getTime())));

    const plannedDays = (isFinite(dueAt.getTime()) && isFinite(loanAt.getTime())) ? daysBetween(loanAt, dueAt) : '-';
    // Only show duration until delivery when actually returned; otherwise show '-'
    const untilReturnDays = (isReturned && retAt && isFinite(retAt.getTime()))
      ? daysBetween(loanAt, retAt)
      : '-';

    // Delay days: if returned → max(0, return - due). If not returned and overdue → days since due. Otherwise '-'
    let delayDays = '-';
    if (isReturned && retAt && isFinite(retAt.getTime()) && isFinite(dueAt.getTime())) {
      delayDays = daysBetween(dueAt, retAt);
    } else if (!isReturned && isFinite(dueAt.getTime()) && now > dueAt) {
      delayDays = daysBetween(dueAt, now);
    }

    return {
      first,
      last,
      grade,
      major,
      loanDate: isFinite(loanAt.getTime()) ? formatDateHuman(loanAt) : '-',
      returnDate: retAt && isFinite(retAt.getTime()) ? formatDateHuman(retAt) : '-',
      plannedDays,
      untilReturnDays,
      delayDays,
    };
  });
}

function renderHistoryTable(rows) {
  const tbody = $('#history-table tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!rows || rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--muted);">موردی یافت نشد</td></tr>';
    return;
  }
  for (const r of rows) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.first}</td>
      <td>${r.last}</td>
      <td>${r.grade || '-'}</td>
      <td>${r.major || '-'}</td>
      <td>${r.loanDate}</td>
      <td>${r.returnDate}</td>
      <td>${r.plannedDays}</td>
      <td>${r.untilReturnDays}</td>
      <td>${r.delayDays}</td>
    `;
    tbody.appendChild(tr);
  }
}

function getReportFilters() {
  const nameQ = $('#report-search-name')?.value || '';
  const grade = $('#report-filter-grade')?.value || '';
  const major = $('#report-filter-major')?.value || '';
  return { nameQ, grade, major };
}

async function updateReports() {
  await ensureHistoryCache();
  const filters = getReportFilters();
  const filtered = applyReportFilters(HISTORY_CACHE, filters);
  HISTORY_VIEW = mapHistoryRows(filtered);
  renderHistoryTable(HISTORY_VIEW);
}

function exportHistoryCSV() {
  const headers = ['نام','نام خانوادگی','پایه','رشته','تاریخ امانت','تاریخ بازگشت','مدت امانت (روز)','مدت تا تحویل (روز)','تاخیر (روز)'];
  const lines = [headers, ...HISTORY_VIEW.map(r => [r.first, r.last, r.grade || '-', r.major || '-', r.loanDate, r.returnDate, r.plannedDays, r.untilReturnDays, r.delayDays])];
  const csv = lines.map(row => row.map(v => '"' + String(v ?? '').replace(/"/g, '""') + '"').join(',')).join('\r\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'library-history.csv';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
}

function initReports() {
  const search = $('#report-search-name');
  const grade = $('#report-filter-grade');
  const major = $('#report-filter-major');
  const exportBtn = $('#btn-export-report');

  if (search) search.addEventListener('input', debounce(updateReports, 250));
  if (grade) grade.addEventListener('change', updateReports);
  if (major) major.addEventListener('change', updateReports);
  if (exportBtn) exportBtn.addEventListener('click', () => {
    if (!HISTORY_VIEW || HISTORY_VIEW.length === 0) {
      showToast('موردی برای خروجی وجود ندارد', 'error');
      return;
    }
    exportHistoryCSV();
  });
}

function initUploadBooksExcel() {
  const form = $('#form-upload-books-excel');
  if (!form) return;
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const fileInput = form.querySelector('input[type="file"]');
    const file = fileInput.files[0];
    
    if (!file) {
      showToast('لطفاً فایل را انتخاب کنید', 'error');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch(API.books.uploadExcel, {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'خطا در آپلود فایل');
      }
      
      const result = await res.json();
      showToast(`${result.total_created} کتاب ثبت شد${result.total_skipped > 0 ? ` و ${result.total_skipped} تکراری نادیده گرفته شد` : ''}`, 'success');
      
      if (result.errors && result.errors.length > 0) {
        console.warn('Excel import errors:', result.errors);
      }
      
      form.reset();
      await loadCategories(); // Reload categories in case new ones were created
    } catch (err) {
      showToast(String(err.message || err), 'error');
    }
  });
}

function initUploadStudentsExcel() {
  const form = $('#form-upload-students-excel');
  if (!form) return;
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const fileInput = form.querySelector('input[type="file"]');
    const file = fileInput.files[0];
    
    if (!file) {
      showToast('لطفاً فایل را انتخاب کنید', 'error');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch(API.students.uploadExcel, {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'خطا در آپلود فایل');
      }
      
      const result = await res.json();
      showToast(`${result.total_created} دانش‌آموز ثبت شد${result.total_skipped > 0 ? ` و ${result.total_skipped} تکراری نادیده گرفته شد` : ''}`, 'success');
      
      if (result.errors && result.errors.length > 0) {
        console.warn('Excel import errors:', result.errors);
      }
      
      form.reset();
      await loadStudents(); // Reload students table
    } catch (err) {
      showToast(String(err.message || err), 'error');
    }
  });
}

// Animated background: diagonal lines with varying fonts and sizes
function initAnimatedBackground() {
  const host = document.querySelector('.bg-animated');
  if (!host) return;
  const paragraph = `کتابخانه یکی از مهم‌ترین مراکز فرهنگی و علمی هر جامعه است که نقش اساسی در گسترش دانش و ارتقای سطح آگاهی افراد ایفا می‌کند. در کتابخانه‌ها منابع متنوعی مانند کتاب، مجله، روزنامه، پایان‌نامه، مقالات علمی و حتی منابع دیجیتال گردآوری و در اختیار علاقه‌مندان قرار می‌گیرد. کتابخانه تنها محلی برای نگهداری کتاب‌ها نیست، بلکه محیطی آرام و الهام‌بخش برای مطالعه، پژوهش و یادگیری مادام‌العمر است. بسیاری از کتابخانه‌ها علاوه بر خدمات امانت کتاب، امکاناتی مانند سالن مطالعه، دسترسی به اینترنت، آرشیو دیجیتال و برگزاری کارگاه‌های آموزشی را نیز فراهم می‌کنند. وجود کتابخانه در یک جامعه، نمادی از اهمیت به فرهنگ، آموزش و پرورش است. کتابخانه‌ها پلی میان گذشته و آینده‌اند؛ جایی که میراث مکتوب بشر حفظ می‌شود و در اختیار نسل‌های آینده قرار می‌گیرد. به همین دلیل، گسترش و حمایت از کتابخانه‌ها، سرمایه‌گذاری بر روی آینده‌ای روشن و آگاهانه است.`;
  const words = paragraph.split(/\s+/).filter(Boolean);
  const fonts = ['font-vazir', 'font-iransansx', 'font-sahel', 'font-shabnam', 'font-vazirmatn'];
  const sizes = ['size-95', 'size-110', 'size-100', 'size-120', 'size-90'];

  function buildLine(startIndex, count) {
    const line = document.createElement('div');
    line.className = 'bg-line';
    const end = startIndex + count;
    for (let i = startIndex; i < end; i++) {
      const w = words[i % words.length];
      const span = document.createElement('span');
      // Change font every 3 words cycling across fonts
      const fontIdx = Math.floor((i - startIndex) / 3) % fonts.length;
      const sizeIdx = (i - startIndex) % sizes.length;
      span.className = `bg-chunk ${fonts[fontIdx]} ${sizes[sizeIdx]}`;
      span.textContent = w;
      line.appendChild(span);
      // add extra spacing between groups
      if ((i - startIndex + 1) % 3 === 0) {
        const sep = document.createElement('span');
        sep.textContent = '  ';
        line.appendChild(sep);
      }
    }
    return line;
  }

  // Create multiple parallel lines across columns and height
  const columns = 2;               // spread horizontally for fuller presence
  const linesPerCol = 10;          // more lines = denser vertically
  const totalLines = columns * linesPerCol;
  const wordsPerLine = 28;         // fewer words = narrower lines

  for (let c = 0; c < columns; c++) {
    for (let i = 0; i < linesPerCol; i++) {
      const idx = c * linesPerCol + i;
      const l = buildLine(idx * 16, wordsPerLine);
      // distribute from -20vh to 120vh evenly
      const topPct = -20 + (140 * idx) / (totalLines - 1);
      l.style.top = `calc(${topPct}vh)`;
      // shift columns horizontally
      l.style.right = c === 0 ? '-12vw' : '18vw';
      // stagger animation delays
      l.style.setProperty('--delay', `${-(idx * 5 + c * 3)}s`);
      host.appendChild(l);
    }
  }
}

function initLogout() {
  const logoutBtn = $('#logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      if (confirm('آیا مطمئن هستید که می‌خواهید خارج شوید؟')) {
        sessionStorage.removeItem('library_authenticated');
        sessionStorage.removeItem('library_login_time');
        window.location.href = './login.html';
      }
    });
  }
}

async function bootstrap() {
  initTabs();
  initBookSearch();
  initDueDateCalculator();
  initAddBookForm();
  initCreateLoanForm();
  initAddStudentForm();
  initLoanFilters();
  initReports();
  initUploadBooksExcel();
  initUploadStudentsExcel();
  initLogout();
  initAnimatedBackground();
  
  await Promise.all([loadCategories(), loadStudents(), loadLoans()]);
}

// Initialize the application when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootstrap);
} else {
  bootstrap();
}
