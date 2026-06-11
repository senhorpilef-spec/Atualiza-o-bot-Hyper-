import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import traceback
import os

# 🔒 Puxando a chave de forma segura por variável de ambiente
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("⚠️ AVISO: GEMINI_API_KEY não configurada! A Aqua não vai funcionar.")
else:
    genai.configure(api_key=GEMINI_KEY)


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO
        self.CRIADOR_ID = 569633804537430036

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignora mensagens de outros bots
        if message.author.bot:
            return

        # 2. Verificar gatilhos (Menção ao nome ou Reply)
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

        # 3. Trava de segurança por ID
        if message.author.id != self.CRIADOR_ID:
            await message.reply("Apenas o criador Geraldão pode usar a minha IA.")
            return

        if not GEMINI_KEY:
            await message.reply("Erro: GEMINI_API_KEY não configurada no sistema.")
            return

        # Ativa o indicador de "digitando"
        async with message.channel.typing():
            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                prompt_sistema = f"""
                Você é a Aqua, uma inteligência artificial administradora integrada diretamente no servidor de Discord.
                Responda ao Geraldão sobre o seguinte pedido: "{message.content}"
                
                Sua resposta deve seguir OBRIGATORIAMENTE este formato exato separado por |||:
                
                [TEXTO]
                Sua resposta conversacional normal aqui.
                |||
                [CODIGO]
                Código em Python puro usando a biblioteca discord.py para executar a ação (se aplicável).
                
                Regras:
                - Se ele pedir uma informação ou ação técnica, use o código para responder direto via `await message.reply()`.
                - Se for só conversa, deixe a área [CODIGO] vazia.
                - Nunca use blocos de markdown (```py) no código.
                """

                # 🔥 SOLUÇÃO DO CONGELAMENTO: Executa a chamada da IA numa Thread separada (Não trava o Discord)
                loop = asyncio.get_event_loop()
                
                try:
                    # Define um limite de 12 segundos para a IA responder
                    response = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: model.generate_content(prompt_sistema)),
                        timeout=12.0
                    )
                except asyncio.TimeoutError:
                    await message.reply("⏳ A API do Gemini demorou muito para responder. Tente novamente.")
                    return

                resposta_completa = response.text
                texto_final = ""
                codigo_gerado = ""
                
                # Divisão do conteúdo
                if "|||" in resposta_completa:
                    partes = resposta_completa.split("|||")
                    texto_final = partes[0].replace("[TEXTO]", "").strip()
                    codigo_gerado = partes[1].replace("[CODIGO]", "").strip()
                else:
                    texto_final = resposta_completa.strip()

                # Se gerou código, executa de forma segura
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

                # Envia o texto se houver
                if texto_final and texto_final.strip() and (not codigo_gerado or not codigo_gerado.strip()):
                    await message.reply(texto_final)
                    
            except Exception as e:
                erro = traceback.format_exc()
                print(f"Erro interno na Aqua:\n{erro}")
                await message.reply(f"❌ Ocorreu um erro ao processar o comando:\n```py\n{str(e)}\n```")


async def setup(bot):
    await bot.add_cog(AquaCog(bot))
                
