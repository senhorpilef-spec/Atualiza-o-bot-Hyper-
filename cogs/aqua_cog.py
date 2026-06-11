import discord
from discord.ext import commands
import google.generativeai as genai
import json
import traceback
import os

# 🔒 Puxando a chave de forma segura por variável de ambiente
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("⚠️ AVISO: GEMINI_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")
else:
    genai.configure(api_key=GEMINI_KEY)


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO (APENAS VOCÊ MANDA)
        self.CRIADOR_ID = 569633804537430036

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignora mensagens enviadas por outros bots
        if message.author.bot:
            return

        # Verificar se a mensagem é um gatilho para a Aqua
        e_gatilho_aqua = False
        
        # Cenário A: O nome Aqua está na mensagem
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
            
        # Cenário B: É um Reply (resposta) para uma mensagem que a própria Aqua mandao
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        # Se não mencionou a Aqua e não é um Reply para ela, ignora e segue em frente
        if not e_gatilho_aqua:
            return

        # 3. Trava Máxima de Segurança por ID de Usuário
        if message.author.id != self.CRIADOR_ID:
            await message.reply("Apenas o criador Geraldão pode usar a minha IA, pois executo ordens críticas.")
            return

        if not GEMINI_KEY:
            await message.reply("Erro: A chave de API da Aqua não foi configurada no sistema.")
            return

        # Mostra no Discord que ela está a responder (Modo Chat IA)
        async with message.channel.typing():
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt_sistema = f"""
            Você é a Aqua, uma inteligência artificial administradora integrada diretamente no servidor de Discord.
            O criador supremo Geraldão deu-te a seguinte ordem ou pergunta em linguagem natural: "{message.content}"
            
            Analise rigorosamente o pedido e responda ESTRITAMENTE em formato JSON com duas chaves:
            1. "codigo": Linhas de código limpas em Python puro utilizando a biblioteca discord.py para realizar rigorosamente a ação solicitada ou buscar a informação técnica que ele quer saber.
            2. "frase_sucesso": Uma resposta em formato de texto normal (estilo IA conversacional) conversando diretamente com o Geraldão, informando de forma natural o que foi feito ou respondendo diretamente à pergunta dele com os dados obtidos.
            
            Regras cruciais para buscar informações ou executar ações no "codigo":
            - Você tem disponíveis as variáveis: `message` (objeto da mensagem), `guild` (objeto do servidor) e `bot` (objeto do bot).
            - Se ele perguntar algo sobre o servidor (ex: quem é o dono/posse, quantos membros têm, quando foi criado), use o código para extrair isso e envie o texto final em "frase_sucesso". Exemplo de lógica para posse: `guild.owner`.
            - Use `await` para todas as funções assíncronas do discord.py.
            - Se precisar usar loops, certifique-se de manter a indentação correta em Python.
            - Nunca inclua marcações de markdown (como ```py) dentro do valor do JSON.
            - Se o pedido for apenas uma conversa que não dependa de dados do servidor ou ações, deixe a chave "codigo" totalmente vazia ("").
            
            Responda APENAS o JSON estruturado, sem nenhum texto antes ou depois dele.
            """
            
            try:
                response = model.generate_content(
                    prompt_sistema,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # Desembrulha o JSON retornado pela IA
                dados_ia = json.loads(response.text)
                codigo_gerado = dados_ia.get("codigo", "")
                frase_sucesso = dados_ia.get("frase_sucesso", "Ordem processada.")
                
                # Se houver código técnico para executar ou buscar informações, roda IMEDIATAMENTE
                if codigo_gerado and codigo_gerado.strip():
                    ambiente_execucao = {
                        "discord": discord,
                        "message": message,
                        "guild": message.guild,
                        "bot": self.bot
                    }
                    
                    # Monta e isola a execução da função assíncrona dinamicamente
                    linhas_codigo = []
                    for linha in codigo_gerado.split('\n'):
                        linhas_codigo.append(f"    {linha}")
                    
                    codigo_final = "async def _executar_ia(message, guild, bot):\n" + "\n".join(linhas_codigo)
                    
                    # Executa o interpretador nos bastidores
                    exec(codigo_final, ambiente_execucao)
                    await ambiente_execucao["_executar_ia"](message, message.guild, self.bot)

                # Dá o .reply direto com o texto natural da IA (Sem Embed, Sem Detalhes Técnicos)
                await message.reply(frase_sucesso)
                
            except Exception as e:
                erro = traceback.format_exc()
                await message.reply(f"❌ Ocorreu um erro interno ao processar ou executar o comando:\n```py\n{erro}\n```")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
            
