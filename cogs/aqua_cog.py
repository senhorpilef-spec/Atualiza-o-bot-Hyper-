import discord
from discord.ext import commands
from groq import Groq
import asyncio
import traceback
import os
import random

# 🔒 Puxando a chave da Groq de forma segura por variável de ambiente
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("⚠️ AVISO: GROQ_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO
        self.CRIADOR_ID = 569633804537430036
        
        # 🛡️ Sistema de controle anti-flood para usuários não autorizados
        self.tentativas_usuarios = {}
        
        # 🎲 Duas respostas simples e diretas de negação (sem exaltação)
        self.respostas_negacao = [
            "Acesso negado. O Geraldão é o dono deste bot e apenas ele tem permissão para usá-lo.",
            "Comando cancelado. Este sistema responde apenas às ordens do dono, o Geraldão."
        ]
        print("🤖 [AquaCog] Motor Groq de Execução Dinâmica Corrigido e Ativado!")

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

        # 3. Trava Máxima de Segurança por ID de Usuário (Com limite de 2 respostas anti-flood)
        if message.author.id != self.CRIADOR_ID:
            user_id = message.author.id
            vezes_usadas = self.tentativas_usuarios.get(user_id, 0)
            
            if vezes_usadas >= 2:
                return
            
            self.tentativas_usuarios[user_id] = vezes_usadas + 1
            resposta_escolhida = random.choice(self.respostas_negacao)
            await message.reply(resposta_escolhida)
            return

        if not GROQ_KEY:
            await message.reply("Erro: A chave de API da Groq (GROQ_API_KEY) não foi configurada no sistema.")
            return

        # Mostra no Discord que ela está a responder (Modo Chat IA)
        async with message.channel.typing():
            try:
                # Inicializa o cliente da Groq
                client = Groq(api_key=GROQ_KEY)
                
                # Mapeia os usuários que você mencionou na mensagem para a IA saber o ID na hora
                mencionados_dados = []
                for m in message.mentions:
                    mencionados_dados.append(f"Nome/Nickname: {m.name} (ou {m.display_name}), ID: {m.id}")
                info_mencionados = "\n".join(mencionados_dados) if mencionados_dados else "Nenhum usuário foi marcado diretamente."
                
                # Semente para manter as respostas de conversa criativas e variadas
                semente_aleatoria = random.randint(1, 100000)
                
                prompt_sistema = f"""
                [ID de Variabilidade da Conversa: {semente_aleatoria}]
                Você é a Aqua, uma inteligência artificial administradora viva, dinâmica e perspicaz integrada diretamente no servidor de Discord com poder total (estilo ChatGPT).
                O dono do bot, Geraldão, deu-te a seguinte ordem ou pergunta: "{message.content}"
                
                LISTA DE USUÁRIOS DETECTADOS/MENCIONADOS NA MENSAGEM DO GERALDÃO:
                {info_mencionados}
                
                Instruções de Personalidade:
                - Nunca repita frases feitas ou respostas anteriores de forma mecânica. Varie o vocabulário, invente respostas inteligentes para tudo.
                - Entenda de forma inteligente o que o Geraldão quer dizer, mesmo usando gírias, e passe para código de Discord de fato fazendo acontecer.
                
                Sua resposta deve seguir OBRIGATORIAMENTE este formato exato separados por |||:
                
                [TEXTO]
                Sua resposta conversacional criativa, variada e natural direcionada ao Geraldão.
                |||
                [CODIGO]
                Código em Python puro usando a biblioteca discord.py para executar a ação ou buscar dados no servidor.
                
                Regras cruciais e obrigatórias para o [CODIGO] (Sintaxe Moderna do Discord.py):
                - Escreva o bloco de código de forma direta, linha por linha.
                - IMPORTANTE: NÃO use 'async def' ou 'def' para criar funções! Escreva as linhas diretamente.
                - Você pode usar 'await' diretamente nas linhas de código.
                - Variáveis nativas já disponíveis para você usar diretamente: `message`, `guild`, `bot`, `channel` e `discord`.
                - Como pegar um membro para Banir/Chutar/Mutar: Use o ID fornecido na lista acima se houver. Exemplo: `membro = guild.get_member(ID_NUMERICO_AQUI)`
                - Para Banir: Após pegar o membro, use `await membro.ban(reason="Ordem do Geraldão")` ou `await guild.ban(discord.Object(id=ID_NUMERICO_AQUI))`.
                - Para apagar mensagens do histórico, use loops assíncronos: `async for msg in channel.history(limit=100): await msg.delete()`.
                - Para aplicar castigo/timeout, use `await member.timed_out_until(data_final)`.
                - Para responder dados solicitados, use sempre `await message.reply(sua_resposta)`.
                - Nunca use blocos de código com markdown (```py) na área [CODIGO].
                """

                # Executa a chamada assíncrona para a Groq usando o modelo Llama 3.3
                loop = asyncio.get_event_loop()
                chat_completion = await loop.run_in_executor(
                    None, 
                    lambda: client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt_sistema}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
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
                    # Escopo limpo e direto
                    ambiente_execucao = {
                        "discord": discord,
                        "message": message,
                        "guild": message.guild,
                        "channel": message.channel,
                        "bot": self.bot,
                        "asyncio": asyncio
                    }
                    
                    # 🔥 Nova abordagem indestrutível: Criamos uma função real via string compilada corretamente
                    linhas_codigo = "\n".join([f"    {linha}" for linha in codigo_gerado.split('\n')])
                    codigo_final = f"async def _run_execution():\n{linhas_codigo}"
                    
                    try:
                        # Compila o código dinâmico com segurança
                        local_vars = {}
                        exec(compile(codigo_final, "<string>", "exec"), ambiente_execucao, local_vars)
                        
                        # Executa a função assíncrona gerada dentro do escopo local isolado
                        await local_vars["_run_execution"]()
                        
                    except Exception as erro_execucao:
                        print(f"❌ [Erro de Execução Dinâmica]:\n{traceback.format_exc()}")
                        await message.reply("⚠️ Tive uma pequena falha na sintaxe desse comando. Estou ajustando meus parâmetros para tentar novamente de forma inteligente.")
                        return

                # Se for apenas uma conversa, envia o texto conversacional único gerado
                if texto_final and texto_final.strip():
                    if not codigo_gerado or "message.reply" not in codigo_gerado:
                        await message.reply(texto_final)
                    
            except Exception as e:
                erro = traceback.format_exc()
                print(f"Erro interno estrutural na Aqua (Groq):\n{erro}")
                await message.reply("❌ Ocorreu um erro estrutural interno. Meus sistemas de processamento foram reiniciados.")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
            
