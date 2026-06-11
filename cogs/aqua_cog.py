import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
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

        # 2. Verificar se a mensagem é um gatilho para a Aqua
        e_gatilho_aqua = False
        
        # Cenário A: O nome Aqua está na mensagem
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
            
        # Cenário B: É um Reply (resposta) para uma mensagem que a própria Aqua mandou
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        # Se não é para a Aqua, ignora completamente
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
            try:
                # 🚀 Definindo a lista de modelos suportados para tentar o que estiver livre na sua conta grátis
                modelos_para_tentar = ["gemini-2.5-flash", "gemini-2.5-pro"]
                response = None
                erro_acumulado = ""

                prompt_sistema = f"""
                Você é a Aqua, uma inteligência artificial administradora integrada diretamente no servidor de Discord.
                O criador supremo Geraldão deu-te a seguinte ordem ou pergunta: "{message.content}"
                
                Sua resposta deve seguir OBRIGATORIAMENTE este formato exato separados por |||:
                
                [TEXTO]
                Sua resposta conversacional normal aqui, conversando diretamente com o Geraldão.
                |||
                [CODIGO]
                Código em Python puro usando a biblioteca discord.py para executar a ação ou buscar dados no servidor.
                
                Regras cruciais:
                - Se ele pedir para buscar uma informação (ex: quem é o dono), use o código para responder direto com `await message.reply()`. Se fizer isso, deixe a área [TEXTO] curta ou vazia.
                - Se for apenas uma conversa fiada ou saudação, deixe a área [CODIGO] totalmente vazia.
                - Variáveis disponíveis: `message`, `guild` e `bot`.
                - Nunca use blocos de código com markdown (```py) na área [CODIGO].
                - Use `await` para funções assíncronas do discord.py.
                """

                loop = asyncio.get_event_loop()

                # Tenta rodar com o 2.5-flash. Se der erro de cota (429), ele pula pro pro de forma automática.
                for nome_modelo in modelos_para_tentar:
                    try:
                        model = genai.GenerativeModel(nome_modelo)
                        response = await asyncio.wait_for(
                            loop.run_in_executor(None, lambda: model.generate_content(prompt_sistema)),
                            timeout=15.0
                        )
                        if response:
                            break
                    except Exception as e_modelo:
                        erro_acumulado += f"\n- {nome_modelo}: {str(e_modelo)}"
                        continue

                if not response:
                    await message.reply(f"❌ Todos os modelos gratuitos falharam ou atingiram o limite diário de requisições:{erro_acumulado}")
                    return

                resposta_completa = response.text
                texto_final = ""
                codigo_gerado = ""
                
                # Divisão segura do conteúdo gerado
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
                        "bot": self.bot
                    }
                    
                    linhas_codigo = [f"    {linha}" for list_linha in codigo_gerado.split('\n') for linha in [list_linha] if linha]
                    codigo_final = "async def _executar_ia(message, guild, bot):\n" + "\n".join(linhas_codigo)
                    
                    local_vars = {}
                    exec(codigo_final, ambiente_execucao, local_vars)
                    await ambiente_execucao["_executar_ia"](message, message.guild, self.bot)

                # Se for apenas uma conversa normal, envia o texto conversacional
                if texto_final and texto_final.strip() and (not codigo_gerado or not codigo_gerado.strip()):
                    await message.reply(texto_final)
                    
            except Exception as e:
                erro = traceback.format_exc()
                print(f"Erro interno na Aqua:\n{erro}")
                await message.reply(f"❌ Ocorreu um erro interno ao processar:\n
```py\n{str(e)}\n```")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
                
