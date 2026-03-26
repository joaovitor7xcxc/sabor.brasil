// pegar usuario do backend
let user = null;

try {
    const data = document.body.getAttribute("data-user");
    user = JSON.parse(data);
} catch {
    user = null;
}

// elementos
const btnLogin = document.getElementById("btn-login");
const btnCadastrar = document.getElementById("btn-cadastrar");
const btnSair = document.getElementById("btn-sair");
const userInfo = document.getElementById("user-info");
const modal = document.getElementById("modal");

// topo
function atualizarTopo(){
    if(user){
        btnLogin.style.display = "none";
        btnCadastrar.style.display = "none";
        btnSair.style.display = "inline";
        userInfo.innerText = "@" + user.nickname;
    }
}
atualizarTopo();

// modal
function abrirModalLogin(){
    modal.style.display = "flex";
    mostrarLogin();
}

function abrirModalCadastro(){
    modal.style.display = "flex";
    mostrarCadastro();
}

function fecharModal(){
    modal.style.display = "none";
}

function mostrarLogin(){
    document.getElementById("login-box").style.display = "block";
    document.getElementById("cadastro-box").style.display = "none";
}

function mostrarCadastro(){
    document.getElementById("login-box").style.display = "none";
    document.getElementById("cadastro-box").style.display = "block";
}

// login
async function fazerLogin(){
    const nickname = document.getElementById("login-user").value.trim();
    const senha = document.getElementById("login-pass").value.trim();

    const res = await fetch("/login", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({nickname, senha})
    });

    const data = await res.json();

    if(res.ok){
        location.reload();
    } else {
        alert(data.erro);
    }
}

// cadastro
async function cadastrar(){
    const nickname = document.getElementById("cad-user").value.trim();
    const senha = document.getElementById("cad-pass").value.trim();

    const res = await fetch("/cadastrar", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({nickname, senha})
    });

    const data = await res.json();

    if(res.ok){
        alert("Cadastro realizado!");
        mostrarLogin();
    } else {
        alert(data.erro);
    }
}

// logout
async function logout(){
    await fetch("/logout", {method:"POST"});
    location.reload();
}

// curtir
async function curtir(id, btn){
    if(!user){
        abrirModalLogin();
        return;
    }

    const res = await fetch(`/curtir/${id}`, {method:"POST"});
    const data = await res.json();

    if(res.ok){
        btn.querySelector("span").innerText = data.total_curtidas;
    }
}

// comentarios
function abrirComentarios(id){
    if(!user){
        abrirModalLogin();
        return;
    }

    document.getElementById("c-"+id).classList.toggle("show");
}

async function comentar(id){
    const texto = document.getElementById("input-"+id).value;

    const res = await fetch(`/comentar/${id}`, {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({texto})
    });

    if(res.ok){
        location.reload();
    }
}

async function removerComentario(id){
    const res = await fetch(`/comentario/${id}`, {method:"DELETE"});
    if(res.ok){
        document.getElementById("cm-"+id).remove();
    }
}

// adicionar receita
function abrirModalAdicionar(){
    document.getElementById("modal-adicionar").style.display = "flex";
}

function fecharModalAdicionar(){
    document.getElementById("modal-adicionar").style.display = "none";
}

async function adicionarReceita(){
    const titulo = document.getElementById("titulo-receita").value;
    const descricao = document.getElementById("descricao-receita").value;
    const imagem = document.getElementById("imagem-receita").value;

    const res = await fetch("/adicionar_receita", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({titulo, descricao, imagem})
    });

    if(res.ok){
        location.reload();
    }
}

// deletar receita
async function deletarReceita(id){
    const res = await fetch(`/deletar_receita/${id}`, {method:"DELETE"});
    if(res.ok){
        location.reload();
    }
}