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

        # Mostra no Discord que ela está a processar
        async with message.channel.typing():
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt_sistema = f"""
            Você é a Aqua, uma inteligência artificial administradora integrada diretamente no servidor de Discord.
            O criador supremo Geraldão deu-te a seguinte ordem ou pergunta: "{message.content}"
            
            Responda ESTRITAMENTE em formato JSON com duas chaves:
            1. "codigo": Código em Python puro usando discord.py para executar a ação ou responder à pergunta técnica (ex: se ele perguntar o dono, use `await message.reply(f"O dono é {{guild.owner.mention}}")`). Se for apenas uma conversa fiada/saudação sem necessidade de comandos, deixe vazio "".
            2. "frase_sucesso": O texto normal de resposta conversacional que você enviará caso o "codigo" esteja vazio. Se o "codigo" já for enviar uma resposta técnica por conta própria, você pode deixar esta frase curta ou vazia.
            
            Regras:
            - Variáveis disponíveis: `message`, `guild` e `bot`.
            - Use `await` para funções assíncronas do discord.py.
            - Nunca inclua marcações de markdown (```py) no JSON.
            - Responda APENAS o JSON.
            """
            
            try:
                response = model.generate_content(
                    prompt_sistema,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                dados_ia = json.loads(response.text)
                codigo_gerado = dados_ia.get("codigo", "")
                frase_sucesso = dados_ia.get("frase_sucesso", "")
                
                # Executa o código se houver
                if codigo_gerado and codigo_gerado.strip():
                    ambiente_execucao = {
                        "discord": discord,
                        "message": message,
                        "guild": message.guild,
                        "bot": self.bot
                    }
                    
                    linhas_codigo = [f"    {linha}" for linha in codigo_gerado.split('\n')]
                    codigo_final = "async def _executar_ia(message, guild, bot):\n" + "\n".join(linhas_codigo)
                    
                    local_vars = {}
                    exec(codigo_final, ambiente_execucao, local_vars)
                    await ambiente_execucao["_executar_ia"](message, message.guild, self.bot)
                
                # Se não rodou código com resposta própria, envia a frase normal
                elif frase_sucesso:
                    await message.reply(frase_sucesso)
                    
            except Exception as e:
                erro = traceback.format_exc()
                await message.reply(f"❌ Ocorreu um erro ao processar:\n```py\n{erro}\n```")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
            
