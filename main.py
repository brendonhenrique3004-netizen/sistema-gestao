import os, secrets, csv, io
from datetime import datetime
from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Integer, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gestao_cargas.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("Configure ADMIN_PASSWORD nas variáveis de ambiente antes de iniciar.")

class Base(DeclarativeBase): pass

class Freight(Base):
    __tablename__ = "freights"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    operational_status: Mapped[str] = mapped_column(String(60), default="Em aberto")
    registration_date: Mapped[str] = mapped_column(String(20), default="")
    driver: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    vehicle: Mapped[str] = mapped_column(String(80), default="")
    plate: Mapped[str] = mapped_column(String(20), default="")
    product: Mapped[str] = mapped_column(String(100), default="")
    pickup: Mapped[str] = mapped_column(String(180), default="")
    delivery: Mapped[str] = mapped_column(String(180), default="")
    intermediate: Mapped[str] = mapped_column(String(180), default="")
    loading_date: Mapped[str] = mapped_column(String(20), default="")
    delivery_date: Mapped[str] = mapped_column(String(20), default="")
    outbound_weight: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    invoice_weight: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    ticket_received: Mapped[str] = mapped_column(String(10), default="Não")
    delivery_doc_received: Mapped[str] = mapped_column(String(10), default="Não")
    bank: Mapped[str] = mapped_column(String(100), default="")
    beneficiary: Mapped[str] = mapped_column(String(140), default="")
    pix_cnpj: Mapped[str] = mapped_column(String(100), default="")
    freight_total: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    advance_requested: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    advance_authorized: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    advance_paid: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    advance_date: Mapped[str] = mapped_column(String(20), default="")
    advance_receipt: Mapped[str] = mapped_column(String(10), default="Não")
    other_paid: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    expected_payment: Mapped[str] = mapped_column(String(20), default="")
    final_payment_date: Mapped[str] = mapped_column(String(20), default="")
    final_payment_confirmed: Mapped[str] = mapped_column(String(10), default="Não")
    origin: Mapped[str] = mapped_column(String(180), default="")
    refrigerated: Mapped[str] = mapped_column(String(10), default="Não")
    temperature: Mapped[str] = mapped_column(String(30), default="")
    initial_ventilation: Mapped[str] = mapped_column(String(10), default="Não")
    ticket_requested: Mapped[str] = mapped_column(String(10), default="Não")
    docs_to_juazeiro: Mapped[str] = mapped_column(String(10), default="Não")
    final_docs_sent: Mapped[str] = mapped_column(String(10), default="Não")
    delivery_confirmed: Mapped[str] = mapped_column(String(10), default="Não")
    pending: Mapped[str] = mapped_column(Text, default="")
    responsible: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payments: Mapped[list["Payment"]] = relationship(back_populates="freight", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    freight_id: Mapped[int] = mapped_column(ForeignKey("freights.id"))
    kind: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Numeric(12,2))
    date: Mapped[str] = mapped_column(String(20), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    freight: Mapped[Freight] = relationship(back_populates="payments")


INDEX_HTML = r'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JR Sul Cargas | Gestão</title>
<style>
:root{font-family:Arial,sans-serif;color:#17212b;background:#f3f5f7}*{box-sizing:border-box}body{margin:0}.top{background:#102a43;color:white;padding:20px}.top h1{margin:0;font-size:22px}.top p{margin:6px 0 0;color:#d9e2ec}.wrap{max-width:1100px;margin:auto;padding:16px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.card{background:white;border:1px solid #d9e2ec;border-radius:12px;padding:14px;margin-bottom:14px}.stat small{color:#627d98}.stat b{display:block;font-size:22px;margin-top:6px}.actions{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}button,.btn{background:#176b45;color:white;border:0;border-radius:8px;padding:11px 14px;font-weight:bold;cursor:pointer}button.secondary{background:#e5edf4;color:#243b53}input,select,textarea{width:100%;padding:10px;border:1px solid #bcccdc;border-radius:7px;background:white;font:inherit}label{display:block;font-size:13px;color:#486581;margin:8px 0 4px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.wide{grid-column:1/-1}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{text-align:left;padding:10px;border-bottom:1px solid #e5edf4;font-size:13px}th{background:#f0f4f8}.muted{color:#627d98;font-size:13px}.hidden{display:none}.pill{padding:4px 7px;background:#e5edf4;border-radius:20px}.row{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}.notice{background:#fff8e1;border:1px solid #f0d98c;padding:10px;border-radius:8px;font-size:13px;margin:12px 0}@media(max-width:600px){.stats{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.wrap{padding:10px}}
</style></head><body>
<header class="top"><h1>JR SUL CARGAS</h1><p>Sistema de gestão de fretes, operação e financeiro</p></header>
<main class="wrap">
<div class="notice">Acesso protegido por usuário e senha configurados no Render. Registre somente pagamentos efetivamente realizados; valores apenas solicitados ou autorizados não reduzem o saldo.</div>
<section class="stats">
<div class="card stat"><small>Fretes cadastrados</small><b id="count">0</b></div>
<div class="card stat"><small>Frete total</small><b id="total">R$ 0,00</b></div>
<div class="card stat"><small>Saldo pendente</small><b id="balance">R$ 0,00</b></div>
</section>
<div class="actions"><button onclick="newFreight()">+ Novo frete</button><button class="secondary" onclick="load()">Atualizar</button><button class="secondary" onclick="location.href='/api/export.csv'">Exportar CSV</button></div>
<section class="card hidden" id="editor"><div class="row"><h2 id="formTitle">Novo frete</h2><button class="secondary" onclick="closeForm()">Fechar</button></div>
<form id="freightForm"><input type="hidden" id="dbid">
<div class="grid">
<div><label>ID do frete *</label><input id="code" required placeholder="JRS-AAAAMMDD-001"></div><div><label>Status operacional</label><select id="operational_status"><option>Em aberto</option><option>Carregado</option><option>Em trânsito</option><option>Entregue</option><option>Cancelado</option></select></div>
<div><label>Data do cadastro</label><input id="registration_date" type="date"></div><div><label>Motorista</label><input id="driver"></div>
<div><label>Telefone</label><input id="phone"></div><div><label>Veículo</label><input id="vehicle" placeholder="Truck, Bitruck, Carreta..."></div>
<div><label>Placa</label><input id="plate"></div><div><label>Produto</label><input id="product" placeholder="Limão, laranja, batata..."></div>
<div><label>Coleta</label><input id="pickup"></div><div><label>Entrega final</label><input id="delivery"></div>
<div><label>Destino intermediário</label><input id="intermediate"></div><div><label>Data de carregamento</label><input id="loading_date" type="date"></div>
<div><label>Data de entrega</label><input id="delivery_date" type="date"></div><div><label>Peso de saída (kg)</label><input id="outbound_weight" type="number" step=".01"></div>
<div><label>Peso da nota (kg)</label><input id="invoice_weight" type="number" step=".01"></div><div><label>Ticket de pesagem recebido?</label><select id="ticket_received"><option>Não</option><option>Sim</option></select></div>
<div><label>Documento de entrega recebido?</label><select id="delivery_doc_received"><option>Não</option><option>Sim</option></select></div><div><label>Banco</label><input id="bank"></div>
<div><label>Favorecido</label><input id="beneficiary"></div><div><label>PIX/CNPJ</label><input id="pix_cnpj"></div>
<div><label>Frete total (R$)</label><input id="freight_total" type="number" step=".01"></div><div><label>Adiantamento solicitado (R$)</label><input id="advance_requested" type="number" step=".01"></div>
<div><label>Adiantamento autorizado (R$)</label><input id="advance_authorized" type="number" step=".01"></div><div><label>Adiantamento já pago (R$)</label><input id="advance_paid" type="number" step=".01"></div>
<div><label>Data do adiantamento</label><input id="advance_date" type="date"></div><div><label>Comprovante do adiantamento?</label><select id="advance_receipt"><option>Não</option><option>Sim</option></select></div>
<div><label>Outros pagamentos confirmados (R$)</label><input id="other_paid" type="number" step=".01"></div><div><label>Data prevista de pagamento</label><input id="expected_payment" type="date"></div>
<div><label>Data do pagamento final</label><input id="final_payment_date" type="date"></div><div><label>Pagamento final confirmado?</label><select id="final_payment_confirmed"><option>Não</option><option>Sim</option></select></div>
<div><label>Origem</label><input id="origin"></div><div><label>Veículo frigorífico?</label><select id="refrigerated"><option>Não</option><option>Sim</option></select></div>
<div><label>Temperatura configurada</label><input id="temperature" placeholder="Ex.: 10°C positivo"></div><div><label>Ventilação inicial concluída?</label><select id="initial_ventilation"><option>Não</option><option>Sim</option></select></div>
<div><label>Ticket solicitado?</label><select id="ticket_requested"><option>Não</option><option>Sim</option></select></div><div><label>Documentação até Juazeiro-BA?</label><select id="docs_to_juazeiro"><option>Não</option><option>Sim</option></select></div>
<div><label>Documentação do trecho final enviada?</label><select id="final_docs_sent"><option>Não</option><option>Sim</option></select></div><div><label>Entrega confirmada?</label><select id="delivery_confirmed"><option>Não</option><option>Sim</option></select></div>
<div><label>Responsável</label><input id="responsible"></div><div class="wide"><label>Pendências</label><textarea id="pending" rows="2"></textarea></div>
<div class="wide"><label>Observações</label><textarea id="notes" rows="3"></textarea></div>
</div><div class="actions"><button type="submit">Salvar frete</button></div></form></section>
<section class="card"><div class="row"><h2>Fretes registrados</h2><input id="filter" placeholder="Buscar ID, motorista, placa ou destino" style="max-width:320px" oninput="render()"></div>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Motorista</th><th>Rota</th><th>Status</th><th>Frete</th><th>Pago</th><th>Saldo</th><th>Ações</th></tr></thead><tbody id="rows"><tr><td colspan="8">Carregando...</td></tr></tbody></table></div></section>
<section class="card"><h3>Registrar pagamento</h3><p class="muted">Escolha um frete e registre o valor efetivamente pago. O saldo é recalculado automaticamente.</p>
<div class="grid"><div><label>Frete</label><select id="paymentFreight"></select></div><div><label>Tipo</label><select id="paymentKind"><option>Adiantamento</option><option>Pagamento parcial</option><option>Pagamento final</option></select></div><div><label>Valor pago (R$)</label><input id="paymentAmount" type="number" min=".01" step=".01"></div><div><label>Data do pagamento</label><input id="paymentDate" type="date"></div><div class="wide"><label>Observação / comprovante</label><input id="paymentNote"></div></div><div class="actions"><button onclick="pay()">Registrar pagamento</button></div></section>
<p class="muted">Versão inicial. Faça backups regulares e configure banco de dados persistente antes de usar em produção com dados reais.</p>
</main>
<script>
let data=[];
const money=n=>(Number(n||0)).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
const ids=['code','operational_status','registration_date','driver','phone','vehicle','plate','product','pickup','delivery','intermediate','loading_date','delivery_date','outbound_weight','invoice_weight','ticket_received','delivery_doc_received','bank','beneficiary','pix_cnpj','freight_total','advance_requested','advance_authorized','advance_paid','advance_date','advance_receipt','other_paid','expected_payment','final_payment_date','final_payment_confirmed','origin','refrigerated','temperature','initial_ventilation','ticket_requested','docs_to_juazeiro','final_docs_sent','delivery_confirmed','pending','responsible','notes'];
function val(id){return document.getElementById(id).value}
async function req(url,opts={}){let r=await fetch(url,{...opts,headers:{'Content-Type':'application/json',...(opts.headers||{})}});if(!r.ok){let t=await r.text();throw Error(t||r.statusText)}return r.json()}
async function load(){try{data=await req('/api/freights');render()}catch(e){alert('Não foi possível carregar. Confira usuário e senha ou conexão. '+e.message)}}
function render(){let q=val('filter').toLowerCase();let filtered=data.filter(x=>[x.code,x.driver,x.plate,x.pickup,x.delivery].join(' ').toLowerCase().includes(q));document.getElementById('count').textContent=data.length;document.getElementById('total').textContent=money(data.reduce((a,x)=>a+Number(x.freight_total||0),0));document.getElementById('balance').textContent=money(data.reduce((a,x)=>a+Number(x.balance||0),0));document.getElementById('rows').innerHTML=filtered.map(x=>`<tr><td><b>${esc(x.code)}</b></td><td>${esc(x.driver)}</td><td>${esc(x.pickup)} → ${esc(x.delivery)}</td><td><span class="pill">${esc(x.operational_status)}</span></td><td>${money(x.freight_total)}</td><td>${money(x.paid_total)}</td><td><b>${money(x.balance)}</b></td><td><button class="secondary" onclick="edit(${x.id})">Editar</button> <button class="secondary" onclick="del(${x.id})">Excluir</button></td></tr>`).join('')||'<tr><td colspan="8">Nenhum frete encontrado.</td></tr>';document.getElementById('paymentFreight').innerHTML=data.map(x=>`<option value="${x.id}">${esc(x.code)} — ${esc(x.driver)}</option>`).join('')}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function newFreight(){document.getElementById('freightForm').reset();document.getElementById('dbid').value='';document.getElementById('formTitle').textContent='Novo frete';document.getElementById('editor').classList.remove('hidden');document.getElementById('editor').scrollIntoView()}
function closeForm(){document.getElementById('editor').classList.add('hidden')}
function edit(id){let x=data.find(a=>a.id===id);newFreight();document.getElementById('dbid').value=id;document.getElementById('formTitle').textContent='Editar frete '+x.code;ids.forEach(k=>{if(x[k]!==undefined)document.getElementById(k).value=x[k]??''})}
document.getElementById('freightForm').onsubmit=async e=>{e.preventDefault();let body={};ids.forEach(k=>body[k]=val(k));['outbound_weight','invoice_weight','freight_total','advance_requested','advance_authorized','advance_paid','other_paid'].forEach(k=>body[k]=Number(body[k]||0));try{let id=val('dbid');await req(id?'/api/freights/'+id:'/api/freights',{method:id?'PUT':'POST',body:JSON.stringify(body)});closeForm();await load();alert('Frete salvo.')}catch(e){alert('Erro ao salvar: '+e.message)}};
async function del(id){if(!confirm('Excluir este frete e seu histórico de pagamentos?'))return;try{await req('/api/freights/'+id,{method:'DELETE'});await load()}catch(e){alert(e.message)}}
async function pay(){let id=val('paymentFreight'),amount=Number(val('paymentAmount'));if(!id||!amount||amount<=0){alert('Selecione o frete e informe um valor válido.');return}try{await req('/api/freights/'+id+'/payments',{method:'POST',body:JSON.stringify({kind:val('paymentKind'),amount,date:val('paymentDate'),note:val('paymentNote')})});document.getElementById('paymentAmount').value='';document.getElementById('paymentNote').value='';await load();alert('Pagamento registrado.')}catch(e){alert(e.message)}}
load();
</script></body></html>'''

Base.metadata.create_all(engine)
app = FastAPI(title="Gestão de Cargas - JR Sul Cargas")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

security = HTTPBasic()
def auth(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    ok_pass = secrets.compare_digest(credentials.password, ADMIN_PASSWORD or "")
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Acesso não autorizado", headers={"WWW-Authenticate":"Basic"})
    return credentials.username

class FreightIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    operational_status: str = "Em aberto"
    registration_date: str = ""
    driver: str = ""
    phone: str = ""
    vehicle: str = ""
    plate: str = ""
    product: str = ""
    pickup: str = ""
    delivery: str = ""
    intermediate: str = ""
    loading_date: str = ""
    delivery_date: str = ""
    outbound_weight: float = 0
    invoice_weight: float = 0
    ticket_received: str = "Não"
    delivery_doc_received: str = "Não"
    bank: str = ""
    beneficiary: str = ""
    pix_cnpj: str = ""
    freight_total: float = 0
    advance_requested: float = 0
    advance_authorized: float = 0
    advance_paid: float = 0
    advance_date: str = ""
    advance_receipt: str = "Não"
    other_paid: float = 0
    expected_payment: str = ""
    final_payment_date: str = ""
    final_payment_confirmed: str = "Não"
    origin: str = ""
    refrigerated: str = "Não"
    temperature: str = ""
    initial_ventilation: str = "Não"
    ticket_requested: str = "Não"
    docs_to_juazeiro: str = "Não"
    final_docs_sent: str = "Não"
    delivery_confirmed: str = "Não"
    pending: str = ""
    responsible: str = ""
    notes: str = ""

class PaymentIn(BaseModel):
    kind: str = "Adiantamento"
    amount: float = Field(gt=0)
    date: str = ""
    note: str = ""

def serialize(f):
    logged_payments = sum(float(p.amount or 0) for p in f.payments)
    # Mantém valores migrados/informados nos campos legados e considera o histórico detalhado.
    paid = max(logged_payments, float(f.advance_paid or 0) + float(f.other_paid or 0))
    total = float(f.freight_total or 0)
    return {c:getattr(f,c) for c in FreightIn.model_fields} | {
        "id":f.id, "paid_total":paid, "balance":round(total-paid,2),
        "payments":[{"id":p.id,"kind":p.kind,"amount":float(p.amount),"date":p.date,"note":p.note} for p in f.payments]
    }

@app.get("/")
def home(_=Depends(auth)):
    return HTMLResponse(INDEX_HTML)

@app.get("/api/freights")
def list_freights(_=Depends(auth), db:Session=Depends(get_db)):
    return [serialize(f) for f in db.query(Freight).order_by(Freight.id.desc()).all()]

@app.post("/api/freights")
def create_freight(data:FreightIn, _=Depends(auth), db:Session=Depends(get_db)):
    if db.query(Freight).filter_by(code=data.code).first():
        raise HTTPException(409,"Já existe um frete com este ID.")
    f=Freight(**data.model_dump()); db.add(f); db.commit(); db.refresh(f)
    return serialize(f)

@app.put("/api/freights/{freight_id}")
def update_freight(freight_id:int, data:FreightIn, _=Depends(auth), db:Session=Depends(get_db)):
    f=db.get(Freight,freight_id)
    if not f: raise HTTPException(404,"Frete não encontrado.")
    if data.code != f.code and db.query(Freight).filter_by(code=data.code).first():
        raise HTTPException(409,"Este ID já está em uso.")
    for k,v in data.model_dump().items(): setattr(f,k,v)
    db.commit(); db.refresh(f); return serialize(f)

@app.delete("/api/freights/{freight_id}")
def delete_freight(freight_id:int, _=Depends(auth), db:Session=Depends(get_db)):
    f=db.get(Freight,freight_id)
    if not f: raise HTTPException(404,"Frete não encontrado.")
    db.delete(f); db.commit(); return {"ok":True}

@app.post("/api/freights/{freight_id}/payments")
def add_payment(freight_id:int, data:PaymentIn, _=Depends(auth), db:Session=Depends(get_db)):
    f=db.get(Freight,freight_id)
    if not f: raise HTTPException(404,"Frete não encontrado.")
    p=Payment(freight_id=freight_id,**data.model_dump()); db.add(p)
    if data.kind.lower().startswith("adiant"):
        f.advance_paid=float(f.advance_paid or 0)+data.amount
        f.advance_date=data.date
        f.advance_receipt="Sim" if data.note else f.advance_receipt
    else:
        f.other_paid=float(f.other_paid or 0)+data.amount
        if data.kind.lower().startswith("final"):
            f.final_payment_date=data.date; f.final_payment_confirmed="Sim"
    db.commit(); db.refresh(f); return serialize(f)

@app.get("/api/export.csv")
def export_csv(_=Depends(auth), db:Session=Depends(get_db)):
    out=io.StringIO(); fields=list(FreightIn.model_fields.keys())+["paid_total","balance"]
    writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
    for f in db.query(Freight).order_by(Freight.id).all():
        row=serialize(f); writer.writerow({k:row.get(k,"") for k in fields})
    data=io.BytesIO(out.getvalue().encode("utf-8-sig"))
    return StreamingResponse(data,media_type="text/csv",headers={"Content-Disposition":"attachment; filename=fretes_jr_sul.csv"})
