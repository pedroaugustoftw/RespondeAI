<p align="center">
  <img src="assets/respondeai.png" width="96" alt="Ícone do RespondeAI">
</p>

# RespondeAI

Selecione uma pergunta na tela e receba uma resposta direta em uma janela compacta.

O RespondeAI é um aplicativo para Windows que transcreve capturas localmente e consulta **Groq ou Gemini** para responder. Em questões com figuras, o modelo configurado para imagens recebe a captura e responde diretamente.

<p align="center">
  <img src="docs/images/inicio.png" width="340" alt="Tela inicial do RespondeAI com botão Iniciar e contador de consultas">
  <img src="docs/images/resposta.png" width="400" alt="Exemplo de resposta: Alternativa A, 4, com botões de copiar, nova captura e configurações">
</p>

> As imagens deste README usam dados de demonstração. As respostas da IA podem conter erros; confira o resultado antes de utilizá-lo.

## Baixar e abrir

1. Acesse a seção **Releases** deste repositório e abra a versão mais recente.
2. Em **Assets**, baixe **RespondeAI.exe**, quando disponível.
3. Abra o arquivo e configure a plataforma de IA conforme as instruções abaixo.

**Não precisa instalar Python nem usar instalador.** Para levar o aplicativo a outro computador, copie somente o `.exe` e configure sua chave nesse computador.

| Requisito | Detalhes |
| --- | --- |
| Sistema | Windows 64 bits. O executável atual foi gerado para Windows. |
| Internet | Necessária para consultar Groq ou Gemini. |
| Chave de API | Uma chave própria da plataforma selecionada, com acesso ao modelo e cota disponível. |
| OCR | Incluído no executável; a transcrição acontece no computador. |

A abertura pode levar alguns segundos, pois o executável único extrai seus componentes para uma pasta temporária do Windows. Não há versões prontas para Linux, macOS ou iOS neste projeto.

## Configurar Groq ou Gemini

Clique na **engrenagem → API**.

<p align="center">
  <img src="docs/images/api.png" width="600" alt="Configurações de API com seleção de plataforma, chave, opção Mostrar chave e modelos de texto e imagem">
</p>

1. Em **Plataforma**, escolha **Groq** ou **Gemini**.
2. Cole sua **Chave API**. Use **Mostrar chave** para conferir o conteúdo.
3. Em **Só texto**, informe o identificador do modelo que responderá às questões sem figura.
4. Em **Com imagem**, informe um modelo da mesma plataforma que aceite imagens.
5. Clique em **Salvar**.

Você pode obter uma chave no [console da Groq](https://console.groq.com/keys) ou no [Google AI Studio](https://aistudio.google.com/apikey).

As chaves e os modelos de cada plataforma ficam guardados separadamente. Você pode alternar entre elas sem preencher tudo novamente. O aplicativo usa a plataforma selecionada; não consulta ambas para a mesma pergunta.

Use o **identificador do modelo**, não o endereço de uma página. A disponibilidade, a gratuidade e as cotas dependem da plataforma e da sua conta. O aplicativo não fornece uma chave ou créditos de API.

## Responder a uma pergunta

1. Deixe a pergunta e todas as alternativas visíveis na tela.
2. No RespondeAI, clique em **Iniciar** ou **Novo**.
3. O aplicativo minimiza para você selecionar a área: clique e arraste sobre a pergunta inteira.
4. Solte o mouse e aguarde o processamento. Para desistir da seleção, pressione **Esc**.
5. A resposta aparece no aplicativo. Clique no **ícone de copiar** para copiá-la ou em **Novo** para capturar outra pergunta.

A janela permanece sobre os outros aplicativos até você minimizá-la. O atalho **Ctrl + Shift + X** inicia uma captura quando o RespondeAI está em foco.

Para melhorar a leitura, amplie textos pequenos e inclua o enunciado, as alternativas e as figuras necessárias na mesma seleção.

## Texto e figuras

Em **Configurações → Geral**, escolha o monitor e o modo de captura:

<p align="center">
  <img src="docs/images/configuracoes.png" width="600" alt="Configurações gerais com seleção de monitor, modo de captura e cópia automática">
</p>

| Modo | Comportamento |
| --- | --- |
| **Detectar figuras automaticamente** | Executa OCR local e procura regiões visuais. Envia a captura se detectar uma figura. |
| **Somente texto (não enviar imagem)** | Envia apenas o texto transcrito pelo OCR local. |
| **A questão contém figura ou gráfico** | Envia a captura completa e o texto transcrito ao modelo de imagens. |

A detecção automática pode errar. Se a questão tiver um gráfico ou uma figura importante que não foi reconhecida, selecione o modo manual correspondente.

Quando uma imagem é enviada, ela vai diretamente ao modelo que responde à questão. Não há uma etapa de descrição por um modelo seguida de uma segunda consulta para obter a resposta.

Você também pode ativar **Copiar resposta automaticamente** nessa tela.

## Carregamento e limites

<p align="center">
  <img src="docs/images/carregamento.png" width="400" alt="Tela de carregamento com indicador animado e mensagem Otimizando uso de tokens">
</p>

Em **Configurações → Limite de uso**, defina o **teto diário local**. O contador reúne as tentativas das duas plataformas neste computador; ele não representa o saldo informado pelos provedores. Reenvios e chamadas que falham também podem consumir esse teto.

- **Limite temporário de segundos ou minutos:** o app mostra o carregamento, espera e tenta novamente. Você pode cancelar a espera.
- **Limite diário informado pela plataforma:** o app avisa e interrompe os reenvios automáticos.
- **Teto diário local:** renova à meia-noite do computador.

A mensagem **“Otimizando uso de tokens…”** também aparece durante a espera pela liberação de cota. Ela não significa que o aplicativo consegue remover o limite da plataforma.

Uma resposta já salva pode ser reutilizada para a mesma captura e configuração, sem nova chamada à API.

## Histórico e dados locais

Use o **ícone de histórico** na tela inicial ou **Configurações → Histórico → Abrir histórico** para consultar respostas anteriores.

O botão **Apagar histórico e cache** remove as respostas salvas e mantém o contador de uso.

- As configurações e o histórico ficam em `%LOCALAPPDATA%\RespondeAI`.
- As chaves cadastradas ficam no cofre de credenciais do Windows.
- As capturas não são gravadas pelo aplicativo em arquivos no disco.
- O texto transcrito é enviado à plataforma escolhida. Quando o modo de captura indicar uma figura, a captura completa também é enviada.
- O executável distribuído não inclui suas chaves ou seu histórico. Cada pessoa configura a própria conta.

## Problemas comuns

| Problema | O que conferir |
| --- | --- |
| Chave inválida ou sem permissão | Confira a plataforma escolhida e a chave em **Configurações → API**. |
| Modelo inexistente ou erro de compatibilidade | Confira o identificador, o acesso na sua conta e se o modelo de imagens aceita capturas. |
| OCR não encontrou texto | Amplie a pergunta e selecione uma área nítida. |
| A resposta ignorou uma figura | Selecione **A questão contém figura ou gráfico** e capture novamente. |
| Carregamento após aviso de cota | Aguarde a liberação do limite temporário ou clique em **Cancelar**. |
| Resposta incorreta ou incompleta | Confira se a captura inclui todo o enunciado e as alternativas; compare o resultado com uma fonte confiável. |

## Executar pelo código-fonte

Esta seção é para quem deseja desenvolver ou modificar o programa. Para usar o aplicativo pronto, basta baixar o `.exe` em **Releases**.

O projeto foi testado com Python 3.14 no Windows. Abra um terminal na pasta do projeto e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Na execução pelo código-fonte, o RapidOCR pode baixar os modelos na primeira utilização. Eles já estão incluídos no executável distribuído.

Também é possível fornecer as chaves por `GROQ_API_KEY` ou `GEMINI_API_KEY`. Uma chave salva nas configurações tem prioridade sobre a variável de ambiente correspondente. Nunca inclua chaves nos arquivos publicados no GitHub.

## Gerar o executável

No Windows, com as dependências instaladas e os modelos de OCR já baixados:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller pillow
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

O resultado fica em **`dist/RespondeAI.exe`**, com o ícone e os modelos locais incluídos.

Para publicar uma versão, anexe esse arquivo a uma **Release** do GitHub. As pastas `.venv`, `build` e `dist` já estão no `.gitignore`; o executável é enviado como anexo da Release.

Para atualizar as imagens deste README com dados de demonstração:

```powershell
.\.venv\Scripts\python.exe docs/capture_screenshots.py
```
