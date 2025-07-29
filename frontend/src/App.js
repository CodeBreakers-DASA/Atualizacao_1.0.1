import React, { useState, useEffect, useRef } from 'react';

const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

// Agilidade -> deixei tudo em um arquivo, mas vamos separar por componentes 
function App() {
  // Estados para armazenar os dados do paciente e da análise
  const [nomePaciente, setNomePaciente] = useState('');
  const [idade, setIdade] = useState('');
  const [dataNascimento, setDataNascimento] = useState('');
  const [tipoAnalise, setTipoAnalise] = useState('');
  const [dataAnalise, setDataAnalise] = useState('');
  const [horarioAnalise, setHorarioAnalise] = useState('');

  // Estados para as medidas atuais e as imagens congeladas após captura
  const [medidas, setMedidas] = useState({ camera1: {}, camera2: {} });
  const [imgCapC1, setImgCapC1] = useState(null);
  const [imgCapC2, setImgCapC2] = useState(null);
  const [capturaRealizada, setCapturaRealizada] = useState(false);

  // Estado para histórico das análises salvas
  const [historico, setHistorico] = useState([]);

  // Atualiza as medidas do backend a cada 0.5 segundos para exibir em tempo real
  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${backendUrl}/medidas_atualizadas`)
        .then((res) => res.json())
        .then(setMedidas)
        .catch(console.error);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Função para atualizar o histórico das análises do banco de dados
  const atualizaHistorico = () => {
    fetch(`${backendUrl}/lista_analises`)
      .then((res) => res.json())
      .then(setHistorico)
      .catch(console.error);
  };

  // Busca o histórico ao carregar o componente
  useEffect(() => {
    atualizaHistorico();
  }, []);

  // Função para capturar as imagens 'congeladas' dos vídeos das câmeras
  const capturarImagens = async () => {
    try {
      // Chamadas para backend capturarem e salvar imagens atuais
      const resC1 = await fetch(`${backendUrl}/capturar_imagem_c1`, { method: 'POST' });
      const dataC1 = await resC1.json();
      const resC2 = await fetch(`${backendUrl}/capturar_imagem_c2`, { method: 'POST' });
      const dataC2 = await resC2.json();

      if (dataC1.status === 'sucesso' && dataC2.status === 'sucesso') {
        // Atualiza o estado com a URL das imagens congeladas (com cachebuster timestamp)
        const now = new Date().getTime();
        setImgCapC1(`${backendUrl}/imagem_c1?${now}`);
        setImgCapC2(`${backendUrl}/imagem_c2?${now}`);
        setCapturaRealizada(true);
        alert('Captura realizada!');
      } else {
        alert('Erro ao capturar imagens. Tente novamente.');
      }
    } catch {
      alert('Erro de comunicação com backend ao capturar imagens');
    }
  };

  // Função para salvar análise (dados do paciente + medidas + caminhos imagens) no backend
  const salvarAnalise = () => {
    if (!nomePaciente || !idade || !dataNascimento) {
      alert('Preencha pelo menos nome, idade e data de nascimento.');
      return;
    }
    const payload = {
      nome_paciente: nomePaciente,
      idade,
      data_nascimento: dataNascimento,
      tipo_analise: tipoAnalise,
      data_analise: dataAnalise,
      horario_analise: horarioAnalise,
      altura_cm: medidas.camera2.altura || 0,
      largura_cm: medidas.camera1.largura || 0,
      comprimento_cm: medidas.camera1.comprimento || 0,
      imagem_c1_path: imgCapC1 ? imgCapC1.replace(`${backendUrl}/`, '') : '',
      imagem_c2_path: imgCapC2 ? imgCapC2.replace(`${backendUrl}/`, '') : '',
    };
    fetch(`${backendUrl}/salvar_analise`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'sucesso') {
          alert('Análise salva com sucesso! ID: ' + data.id);
          setCapturaRealizada(false);
          atualizaHistorico();
          // Aqui da para resetar os forms 
        } else {
          alert('Erro ao salvar análise: ' + data.mensagem);
        }
      })
      .catch(() => alert('Erro na comunicação com backend'));
  };

  // Resetar captura para permitir nova medida
  const resetarCaptura = () => {
    setImgCapC1(null);
    setImgCapC2(null);
    setCapturaRealizada(false);
  };

  return (
    <div style={{ padding: 20, minHeight: '100vh', backgroundColor: '#222', color: 'white', fontFamily: 'Arial, sans-serif' }}>
      <h1>Sistema Completo de Medição</h1>

      {/* Formulário dos dados do paciente e análise */}
      <section style={{ marginBottom: 30 }}>
        <h2>Dados do Paciente e Análise</h2>
        <input placeholder="Nome" value={nomePaciente} onChange={(e) => setNomePaciente(e.target.value)} style={{ marginRight: 10 }} />
        <input placeholder="Idade" type="number" value={idade} onChange={(e) => setIdade(e.target.value)} style={{ marginRight: 10, width: 70 }} />
        <input type="date" value={dataNascimento} onChange={(e) => setDataNascimento(e.target.value)} style={{ marginRight: 10 }} />
        <br /><br />
        <input placeholder="Tipo de Análise" value={tipoAnalise} onChange={(e) => setTipoAnalise(e.target.value)} style={{ marginRight: 10, width: 300 }} />
        <input type="date" value={dataAnalise} onChange={(e) => setDataAnalise(e.target.value)} style={{ marginRight: 10 }} />
        <input type="time" value={horarioAnalise} onChange={(e) => setHorarioAnalise(e.target.value)} />
      </section>

      {/* Área de vídeos e medidas */}
      <section style={{ marginBottom: 30 }}>
        <h2>Câmeras e Medidas</h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap' }}>
          <div>
            <h3>Câmera 1 (Largura e Comprimento)</h3>
            <img src={`${backendUrl}/video_feed_1`} alt="Camera 1" style={{ width: 320, border: '2px solid white' }} />
            <p>
              <b>Largura:</b> {medidas.camera1.largura ? medidas.camera1.largura.toFixed(2) : '0.00'} cm<br />
              <b>Comprimento:</b> {medidas.camera1.comprimento ? medidas.camera1.comprimento.toFixed(2) : '0.00'} cm
            </p>
          </div>
          <div>
            <h3>Câmera 2 (Altura)</h3>
            <img src={`${backendUrl}/video_feed_2`} alt="Camera 2" style={{ width: 320, border: '2px solid white' }} />
            <p>
              <b>Altura:</b> {medidas.camera2.altura ? medidas.camera2.altura.toFixed(2) : '0.00'} cm
            </p>
          </div>
        </div>
        {!capturaRealizada ? (
          <button onClick={capturarImagens} style={{ marginTop: 15, padding: '10px 20px', fontSize: 16 }}>
            Capturar Imagens
          </button>
        ) : (
          <>
            <h3>Imagens Capturadas</h3>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap' }}>
              <img src={imgCapC1} alt="Captura Câmera 1" style={{ width: 320, border: '2px solid #0f0' }} />
              <img src={imgCapC2} alt="Captura Câmera 2" style={{ width: 320, border: '2px solid #0f0' }} />
            </div>
            <button onClick={salvarAnalise} style={{ marginTop: 15, marginRight: 10, padding: '10px 20px', fontSize: 16 }}>
              Salvar Análise
            </button>
            <button onClick={resetarCaptura} style={{ marginTop: 15, padding: '10px 20px', fontSize: 16 }}>
              Realizar Nova Captura
            </button>
          </>
        )}
      </section>

      {/* Tabela com o histórico das análises salvas */}
      <section>
        <h2>Histórico de Análises</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', color: 'white' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid white' }}>
              <th>Nome</th>
              <th>Idade</th>
              <th>Nascimento</th>
              <th>Tipo Análise</th>
              <th>Data análise</th>
              <th>Horário</th>
              <th>Altura (cm)</th>
              <th>Largura (cm)</th>
              <th>Comprimento (cm)</th>
              <th>Imagens</th>
              <th>Data Captura</th>
            </tr>
          </thead>
          <tbody>
            {historico.length === 0 ? (
              <tr><td colSpan="11">Nenhuma análise encontrada</td></tr>
            ) : (
              historico.map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid #444' }}>
                  <td>{item.nome_paciente}</td>
                  <td>{item.idade}</td>
                  <td>{item.data_nascimento}</td>
                  <td>{item.tipo_analise}</td>
                  <td>{item.data_analise}</td>
                  <td>{item.horario_analise}</td>
                  <td>{item.altura_cm?.toFixed(2)}</td>
                  <td>{item.largura_cm?.toFixed(2)}</td>
                  <td>{item.comprimento_cm?.toFixed(2)}</td>
                  <td style={{ display: 'flex', gap: 10 }}>
                    {item.imagem_c1_path && <img src={`${backendUrl}/${item.imagem_c1_path}`} alt="C1" width={80} />}
                    {item.imagem_c2_path && <img src={`${backendUrl}/${item.imagem_c2_path}`} alt="C2" width={80} />}
                  </td>
                  <td>{item.data_captura}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default App;
