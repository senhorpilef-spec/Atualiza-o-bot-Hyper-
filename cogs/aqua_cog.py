import discord
from discord.ext import commands
from groq import Groq
import asyncio
import traceback
import os

# 🔒 Puxando a chave da Groq de forma segura por variável de ambiente
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("⚠️ AVISO: GROQ_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO (APENAS VOCÊ MANDA)
        self.CRIADOR_ID = 569633804537430036
        print("🤖 [AquaCog] Sistema Groq Sem Limites Iniciado para o Geraldão!")

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignora mensagens enviadas por outros bots
        if message.author.bot:
            return

        # 2. Verificar se a mensagem é um gatilho para a Aqua
        e_gatilho_aqua = False
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        if not e_gatilho_aqua:
            return

        # 3. Trava Máxima de Segurança por ID de Usuário
        if message.author.id != self.CRIADOR_ID:
            await message.reply("Apenas o criador Geraldão pode usar a minha IA, pois executo ordens críticas.")
            return

        if not GROQ_KEY:
            await message.reply("Erro: A chave de API da Groq (GROQ_API_KEY) não foi configurada no sistema.")
            return

        # Mostra no Discord que ela está a responder (Modo Chat IA)
        async with message.channel.typing():
            try:
                # Inicializa o cliente da Groq
                client = Groq(api_key=GROQ_KEY)
                
                prompt_sistema = f"""
                Você é a Aqua, uma inteligência artificial administradora integrada diretamente no servidor de Discord.
                O criador supremo Geraldão deu-te a seguinte ordem ou pergunta: "{message.content}"
                
                Sua resposta deve seguir OBRIGATORIAMENTE este formato exato separados por |||:
                
                [TEXTO]
                Sua resposta conversacional curta reconhecendo a ordem do Geraldão.
                |||
                [CODIGO]
                Código em Python puro usando a biblioteca discord.py para executar a ação ou buscar dados no servidor.
                
                Regras cruciais para o [CODIGO]:
                - Não crie funções (não use 'def'). Escreva as linhas de código diretamente, uma abaixo da outra.
                - Você pode usar 'await' diretamente nas linhas.
                - Variáveis nativas disponíveis para você usar diretamente: `message`, `guild`, `bot`, `channel` e `discord`.
                - Para responder dados solicitados (como quem é o dono ou listar algo), use sempre `await message.reply(sua_resposta)`.
                - Se a ordem exigir modificar múltiplos canais ou cargos (ex: privar canais, apagar cargos), use estruturas de repetição (for) assíncronas de forma limpa.
                - Nunca use blocos de código com markdown (```py) na área [CODIGO].
                """

                # Executa a chamada assíncrona para a Groq usando o super modelo Llama 3.3
                loop = asyncio.get_event_loop()
                
                # Modelo de alta performance e gratuito da Meta distribuído pela Groq
                chat_completion = await loop.run_in_executor(
                    None, 
                    lambda: client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt_sistema,
                            }
                        ],
                        model="llama-3.3-70b-versatile",
                        temperature=0.3,
                    )
                )

                resposta_completa = chat_completion.choices[0].message.content
                texto_final = ""
                codigo_gerado = ""
                
                if "|||" in resposta_completa:
                    partes = resposta_completa.split("|||")
                    texto_final = partes[0].replace("[TEXTO]", "").strip()
                    codigo_gerado = partes[1].replace("[CODIGO]", "").strip()
                else:
                    texto_final = resposta_completa.strip()

                # Se houver código técnico para executar, roda IMEDIATAMENTE nos bastidores
                if codigo_gerado and codigo_gerado.strip():
                    ambiente_execucao = {
                        "discord": discord,
                        "message": message,
                        "guild": message.guild,
                        "channel": message.channel,
                        "bot": self.bot,
                        "asyncio": asyncio
                    }
                    
                    linhas_codigo = []
                    for linha in codigo_gerado.split('\n'):
                        linhas_codigo.append(f"    {linha}")
                            
                    codigo_final = "async def _executor_direto():\n" + "\n".join(linhas_codigo)
                    
                    try:
                        exec(codigo_final, ambiente_execucao)
                        funcao_assincrona = ambiente_execucao["_executor_direto"]
                        await funcao_assincrona()
                    except Exception as erro_execucao:
                        erro_formatado = traceback.format_exc()
                        await message.reply(f"❌ Erro na execução do script gerado:\n```py\n{erro_formatado}\n```")
                        return

                # Se for apenas uma conversa, envia o texto conversacional
                if texto_final and texto_final.strip():
                    if not codigo_gerado or "message.reply" not in codigo_gerado:
                        await message.reply(texto_final)
                    
            except Exception as e:
                erro = traceback.format_exc()
                print(f"Erro interno na Aqua (Groq):\n{erro}")
                await message.reply(f"❌ Ocorreu um erro estrutural ao processar:\n```py\n{str(e)}\n```")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
                
