// ============================================================
// BARRA DE TOPO — a mesma na home e no catalogo.
// Monta a partir do 'times' do dados.js, entao adicionar um time
// la em cima ja o coloca no menu das duas paginas.
// ============================================================
(function () {
  const CSS_TOPO = `
  :root{
    --topo-bg:#1f1811; --topo-ink:#ffffff; --topo-dim:#a89680;
    --marca:#1f1811; --ouro:#a97f4e; --zap:#0f6b36; --linha:#e3d9c8;
    --papel:#faf6ef;
  }
  #topo *{box-sizing:border-box;}
  .aviso{
    background:var(--topo-bg); color:#ece0cd; overflow:hidden;
    font-size:11px; font-weight:600; letter-spacing:1.6px; text-transform:uppercase;
  }
  .aviso-trilho{
    display:flex; gap:44px; width:max-content;
    padding:9px 0; animation:corre 26s linear infinite;
  }
  .aviso-trilho span{white-space:nowrap;}
  @keyframes corre{from{transform:translateX(0)} to{transform:translateX(-50%)}}
  @media (prefers-reduced-motion:reduce){ .aviso-trilho{animation:none; padding-left:16px;} }

  .barra{
    background:#fff; border-bottom:1px solid var(--linha);
    display:flex; align-items:center; gap:16px;
    padding:14px 18px;
  }
  .marca{
    display:flex; align-items:center; gap:9px;
    font-family:'Playfair Display',Georgia,serif; font-size:22px; letter-spacing:.1px;
    color:var(--marca); text-decoration:none; font-weight:600;
    flex:0 0 auto; line-height:1;
  }
  .marca img{
    width:38px; height:38px; display:block; border-radius:10px; flex:0 0 auto;
  }
  .marca .nome{display:flex; align-items:baseline; gap:5px;}
  .marca b{color:var(--ouro); font-weight:600; font-style:italic;}
  .busca{flex:1; position:relative; display:flex; align-items:center; min-width:0;}
  .busca svg{position:absolute; left:14px; opacity:.4; pointer-events:none;}
  .busca input{
    width:100%; padding:11px 14px 11px 38px; border-radius:10px;
    border:1px solid var(--linha); background:#f3ece0;
    font-size:14px; font-family:'Inter',Arial,sans-serif; color:#1f1811;
  }
  .busca input:focus{outline:none; border-color:#d3c5ad; background:#fff;}
  .zap-topo{
    flex:0 0 auto; display:flex; align-items:center; gap:7px;
    background:var(--zap); color:#fff; text-decoration:none;
    padding:10px 17px; border-radius:10px; font-size:12.5px; font-weight:700;
    letter-spacing:.3px;
    white-space:nowrap;
  }

  .nav{
    background:#fff; border-bottom:1px solid var(--linha);
    position:sticky; top:0; z-index:40;
  }
  .nav-trilho{
    display:flex; align-items:stretch; gap:2px;
    overflow-x:auto; scrollbar-width:none; padding:0 8px;
  }
  .nav-trilho::-webkit-scrollbar{display:none;}
  .nav-item{position:relative; flex:0 0 auto;}
  .nav-link{
    display:flex; align-items:center; gap:5px;
    padding:14px 14px; background:none; border:none;
    font-family:'Inter',Arial,sans-serif; font-size:12px; font-weight:600;
    letter-spacing:1.1px; text-transform:uppercase; color:var(--marca);
    text-decoration:none; cursor:pointer; white-space:nowrap;
    border-bottom:3px solid transparent;
  }
  .nav-link:hover, .nav-item.aberto > .nav-link{border-bottom-color:var(--ouro);}
  .nav-link .seta{font-size:10px; color:var(--topo-dim);}
  .nav-link.destaque{color:var(--ouro);}

  /* O painel NAO pode morar dentro de .nav-trilho: o overflow-x de la
     recorta qualquer coisa posicionada pra fora. Por isso ele fica solto
     em .mega-area, logo abaixo do trilho, ocupando a largura toda. */
  .mega-area{
    display:none; background:#fff; border-top:1px solid var(--linha);
    box-shadow:0 16px 30px rgba(0,0,0,.11);
    max-height:min(70vh, 560px); overflow-y:auto;
  }
  .mega-area.aberto{display:block;}
  .mega{display:none; padding:18px;}
  .mega.ativo{display:block;}
  .mega-cols{
    display:flex; gap:26px; align-items:flex-start; flex-wrap:wrap;
    max-width:1220px; margin:0 auto;
  }
  .mega-col{display:flex; flex-direction:column; min-width:150px;}
  .mega-titulo{
    font-size:10.5px; font-weight:800; letter-spacing:1px; text-transform:uppercase;
    color:var(--marca); padding:0 0 7px; border-bottom:1px solid var(--linha); margin-bottom:6px;
  }
  .mega a{
    padding:6px 4px; font-size:13px; color:#4a4034;
    text-decoration:none; border-radius:6px; white-space:nowrap;
  }
  .mega a:hover{background:#efe6d6; color:var(--marca);}
  .mega a.tudo{font-weight:700; color:var(--marca);}

  @media (max-width:900px){
    .barra{flex-wrap:wrap; gap:10px; padding:12px 14px;}
    .marca{font-size:17px; gap:7px;} .marca img{width:32px; height:32px;}
    .busca{order:3; flex:1 0 100%;}
    .zap-topo{margin-left:auto;}
    .mega{padding:12px 14px 16px;}
    .mega-cols{flex-direction:column; gap:14px;}
    .nav-trilho{flex-wrap:nowrap;}
  }`;

  // ---------------------------------------------------------------- helpers
  const CAT = 'catalogo.html';
  const url = (p) => CAT + '?' + new URLSearchParams(p).toString();
  const el = (tag, cls, txt) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  };

  function coluna(titulo, itens) {
    const c = el('div', 'mega-col');
    c.appendChild(el('div', 'mega-titulo', titulo));
    itens.forEach(([texto, href, tudo]) => {
      const a = el('a', tudo ? 'tudo' : null, texto);
      a.href = href;
      c.appendChild(a);
    });
    return c;
  }

  // o painel vai pra megaArea; o item so guarda a referencia por id
  function itemNav(rotulo, href, colunas, destaque, megaArea, id) {
    const item = el('div', 'nav-item');
    const link = el(href ? 'a' : 'button', 'nav-link' + (destaque ? ' destaque' : ''));
    link.append(rotulo);
    if (href) link.href = href;
    if (!colunas) { item.appendChild(link); return item; }

    link.appendChild(el('span', 'seta', '▾'));
    const mega = el('div', 'mega');
    mega.dataset.mega = id;
    const wrap = el('div', 'mega-cols');
    colunas.forEach(c => wrap.appendChild(c));
    mega.appendChild(wrap);
    megaArea.appendChild(mega);
    item.appendChild(link);

    link.addEventListener('click', (ev) => {
      ev.preventDefault();
      const jaAberto = item.classList.contains('aberto');
      fecharMegas();
      if (!jaAberto) {
        item.classList.add('aberto');
        mega.classList.add('ativo');
        megaArea.classList.add('aberto');
      }
    });
    return item;
  }

  function fecharMegas() {
    document.querySelectorAll('.nav-item.aberto').forEach(i => i.classList.remove('aberto'));
    document.querySelectorAll('.mega.ativo').forEach(m => m.classList.remove('ativo'));
    document.querySelectorAll('.mega-area.aberto').forEach(a => a.classList.remove('aberto'));
  }

  // ------------------------------------------------------------------ topo
  window.montarTopo = function montarTopo(pagina) {
    const alvo = document.getElementById('topo');
    if (!alvo) return;

    const estilo = el('style');
    estilo.textContent = CSS_TOPO;
    document.head.appendChild(estilo);

    // --- faixa de avisos (duplicada pra o loop nao dar salto)
    const avisos = [
      'PEÇAS RARAS E EDIÇÕES FORA DE LINHA', 'RETRÔ COM NOME DE JOGADOR',
      'CLUBES QUE NINGUÉM TEM', 'ENVIO PARA TODO O BRASIL',
      'ATENDIMENTO DIRETO NO WHATSAPP', 'COLEÇÃO 26/27 NO AR'
    ];
    const aviso = el('div', 'aviso');
    const trilho = el('div', 'aviso-trilho');
    avisos.concat(avisos).forEach(t => trilho.appendChild(el('span', null, '• ' + t)));
    aviso.appendChild(trilho);

    // --- barra com marca, busca e whatsapp
    const barra = el('div', 'barra');
    const marca = el('a', 'marca');
    marca.href = 'index.html';
    marca.innerHTML = '<img src="marca-ce.png" alt="" width="38" height="38">'
                    + '<span class="nome">Camisaria Esportiva<b>FC</b></span>';
    const busca = el('div', 'busca');
    busca.innerHTML =
      '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#1f1811" stroke-width="2">' +
      '<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' +
      '<input type="search" placeholder="Buscar time, seleção, liga ou ano...">';
    const campo = busca.querySelector('input');
    const alvoBusca = document.getElementById('search-input');
    if (pagina === 'catalogo' && alvoBusca) {
      // ja estamos no catalogo: filtra ao vivo, sem recarregar a pagina
      campo.value = new URLSearchParams(location.search).get('busca') || '';
      campo.addEventListener('input', () => {
        alvoBusca.value = campo.value;
        alvoBusca.dispatchEvent(new Event('input'));
      });
    } else {
      campo.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && campo.value.trim()) location.href = url({ busca: campo.value.trim() });
      });
    }
    const zap = el('a', 'zap-topo');
    zap.href = typeof linkZap === 'function'
      ? linkZap('Olá! Vi o catálogo da Camisaria Esportiva FC e quero saber mais.')
      : 'https://wa.me/' + (window.WHATSAPP_NUMERO || '');
    zap.target = '_blank';
    zap.innerHTML =
      '<svg width="13" height="13" viewBox="0 0 32 32" fill="#ffffff"><path d="M16 3C9.4 3 4 8.4 4 15c0 2.4.7 4.6 1.9 6.5L4 29l7.7-1.9A12 12 0 0016 27c6.6 0 12-5.4 12-12S22.6 3 16 3z"/></svg>' +
      'WhatsApp';
    barra.append(marca, busca, zap);

    // --- navegação
    const nav = el('nav', 'nav');
    const navTrilho = el('div', 'nav-trilho');

    const selecoes = times.filter(t => t.selecao);
    const clubes = times.filter(t => !t.selecao);

    // Seleções: uma coluna por grupo (Copa 2026 / Clássicas fora)
    const colsSel = [];
    ['Copa 2026', 'Clássicas fora'].forEach(g => {
      const doGrupo = selecoes.filter(s => s.grupo === g);
      if (!doGrupo.length) return;
      // parte em colunas de 16 pra nao virar uma lista infinita
      for (let i = 0; i < doGrupo.length; i += 16) {
        const fatia = doGrupo.slice(i, i + 16);
        const titulo = i === 0
          ? (g === 'Copa 2026' ? '🏆 Copa do Mundo 2026' : '⭐ Clássicas fora da Copa')
          : ' ';
        const itens = fatia.map(s => [s.nome, url({ time: s.nome })]);
        if (i === 0 && g === 'Copa 2026') itens.unshift(['Todas as seleções', url({ tipo: 'selecao' }), true]);
        colsSel.push(coluna(titulo, itens));
      }
    });

    // Clubes: uma coluna por continente, listando as ligas
    const colsClu = [];
    [...new Set(clubes.map(c => c.continente))].forEach(cont => {
      const ligas = [...new Set(clubes.filter(c => c.continente === cont).map(c => c.liga))];
      const itens = ligas.map(l => [l.split(' · ')[0], url({ liga: l })]);
      if (cont === 'Europa') itens.unshift(['Todos os clubes', url({ tipo: 'clube' }), true]);
      colsClu.push(coluna(cont, itens));
    });

    const megaArea = el('div', 'mega-area');
    navTrilho.append(
      itemNav('Seleções', null, colsSel, false, megaArea, 'selecoes'),
      itemNav('Clubes', null, colsClu, false, megaArea, 'clubes'),
      itemNav('Retrô & Raras', 'camisas-retro.html'),
      itemNav('Kit Infantil', url({ genero: 'infantil' })),
      itemNav('Calções', url({ categoria: 'calcao' })),
      itemNav('Jaquetas', url({ categoria: 'jaqueta' })),
      itemNav('26/27', url({ temporada: '26-27' })),
      itemNav('25/26', url({ temporada: '25-26' })),
      itemNav('Ver tudo', CAT, null, true)
    );
    nav.append(navTrilho, megaArea);

    alvo.append(aviso, barra, nav);

    // clicar fora fecha o mega aberto
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.nav-item') && !e.target.closest('.mega-area')) fecharMegas();
    });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharMegas(); });
  };
})();


// ============================================================
// VOLTAR AO TOPO — em todas as páginas que carregam este arquivo
// ============================================================
// A home tem 4 telas de rolagem, a página de um time tem até 12, e o
// acervo tem 2 mil cartões. Sem isto, voltar ao topo no celular é rolar
// tudo de novo com o dedo — foi a primeira coisa que apareceu quando o
// site foi usado no celular de verdade.
//
// O botão se monta sozinho e injeta o próprio estilo, pra não depender de
// mexer nas 342 páginas geradas. Se a página já trouxer um #ao-topo
// próprio (o catálogo traz), este aqui sai de cena.
(function () {
  'use strict';

  function montar() {
    if (document.getElementById('ao-topo')) return;

    var css = document.createElement('style');
    css.textContent =
      '.ao-topo{position:fixed;right:16px;bottom:74px;z-index:52;width:46px;' +
      'height:46px;border-radius:999px;border:1px solid #e3d9c8;' +
      'background:rgba(255,255,255,.95);color:#1f1811;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'box-shadow:0 5px 16px rgba(31,24,17,.16);opacity:0;pointer-events:none;' +
      'transform:translateY(8px);transition:opacity .18s ease,transform .18s ease}' +
      '.ao-topo.vendo{opacity:1;pointer-events:auto;transform:none}' +
      '.ao-topo:hover{border-color:#a97f4e}';
    document.head.appendChild(css);

    var b = document.createElement('button');
    b.id = 'ao-topo';
    b.className = 'ao-topo';
    b.type = 'button';
    b.setAttribute('aria-label', 'Voltar ao topo');
    b.title = 'Voltar ao topo';
    b.innerHTML =
      '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#1f1811"' +
      ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
      '<line x1="12" y1="19" x2="12" y2="6"/><polyline points="6,12 12,6 18,12"/></svg>';
    b.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.body.appendChild(b);

    // o scroll dispara dezenas de vezes por segundo; sem esta trava o
    // celular fica engasgado só pra decidir se mostra um botão
    var pintando = false;
    window.addEventListener('scroll', function () {
      if (pintando) return;
      pintando = true;
      requestAnimationFrame(function () {
        b.classList.toggle('vendo', window.scrollY > 700);
        pintando = false;
      });
    }, { passive: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', montar);
  } else {
    montar();
  }
})();
